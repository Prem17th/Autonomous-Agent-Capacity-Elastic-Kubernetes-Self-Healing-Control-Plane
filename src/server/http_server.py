"""Streamable HTTP transport adapter for Nasiko Sentinel MCP Server."""

import json
import secrets
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from src.config.settings import Settings
from src.errors.exceptions import ConfigError
from src.logger.logger import get_logger
from src.server.dashboard_html import DASHBOARD_HTML
from src.server.health import get_health_status
from src.server.mcp_server import (
    INTERNAL_ERROR,
    INVALID_REQUEST,
    PARSE_ERROR,
    MCPServer,
)

logger = get_logger("server.http")

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB


class MCPHTTPRequestHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler that routes MCP JSON-RPC 2.0 requests to MCPServer."""

    # Disable default BaseHTTPRequestHandler logging to stderr; use structured logger
    def log_message(self, format: str, *args: Any) -> None:
        pass

    @property
    def server_instance(self) -> "HttpMCPServer":
        return self.server.http_mcp_server  # type: ignore

    def _send_html_response(
        self,
        status_code: int,
        html_content: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Helper to send HTML responses with appropriate headers."""
        body = html_content.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _send_json_response(
        self,
        status_code: int,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Helper to send JSON responses with appropriate headers."""
        try:
            body = json.dumps(data).encode("utf-8")
        except Exception:
            body = json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": INTERNAL_ERROR, "message": "Failed to serialize response"},
            }).encode("utf-8")
            status_code = HTTPStatus.INTERNAL_SERVER_ERROR

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _authenticate(self) -> bool:
        """Validate API Key using constant-time comparison."""
        expected_key = self.server_instance.api_key
        if not expected_key:
            # If no API key is configured (e.g. test mode), allow access
            return True

        # Check Authorization: Bearer <token>
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if secrets.compare_digest(token, expected_key):
                return True

        # Check X-Sentinel-API-Key or X-API-Key headers
        sentinel_key = self.headers.get("X-Sentinel-API-Key", "").strip()
        if sentinel_key and secrets.compare_digest(sentinel_key, expected_key):
            return True

        api_key = self.headers.get("X-API-Key", "").strip()
        if api_key and secrets.compare_digest(api_key, expected_key):
            return True

        return False

    def do_GET(self) -> None:
        """Handle GET requests (e.g. /health and interactive web dashboard)."""
        path = self.path.split("?")[0].rstrip("/")
        accept_header = self.headers.get("Accept", "")

        # Explicit health endpoint
        if path == "/health":
            health_data = get_health_status(
                self.server_instance.settings,
                k8s_connected=self.server_instance.mcp_server.adapter.check_connection(),
                autoscaler_type=self.server_instance.mcp_server.autoscaler_provider.provider_type,
                reasoner_name=(
                    self.server_instance.mcp_server.reasoner.primary_reasoner.reasoner_name
                    if self.server_instance.mcp_server.reasoner.primary_reasoner
                    else "deterministic_fallback"
                ),
            )
            self._send_json_response(HTTPStatus.OK, health_data)
            return

        # Root dashboard endpoint (serves interactive HTML for browser visits)
        if path in {"", "/dashboard"}:
            if "application/json" in accept_header and "text/html" not in accept_header:
                health_data = get_health_status(
                    self.server_instance.settings,
                    k8s_connected=self.server_instance.mcp_server.adapter.check_connection(),
                    autoscaler_type=self.server_instance.mcp_server.autoscaler_provider.provider_type,
                    reasoner_name=(
                        self.server_instance.mcp_server.reasoner.primary_reasoner.reasoner_name
                        if self.server_instance.mcp_server.reasoner.primary_reasoner
                        else "deterministic_fallback"
                    ),
                )
                self._send_json_response(HTTPStatus.OK, health_data)
                return

            self._send_html_response(HTTPStatus.OK, DASHBOARD_HTML)
            return

        self._send_json_response(
            HTTPStatus.NOT_FOUND,
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32601, "message": f"Resource not found: {self.path}"},
            },
        )

    def do_POST(self) -> None:
        """Handle POST requests (MCP JSON-RPC endpoint at /mcp or /)."""
        path = self.path.split("?")[0].rstrip("/")
        if path not in {"", "/mcp"}:
            self._send_json_response(
                HTTPStatus.NOT_FOUND,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32601, "message": f"MCP endpoint not found: {self.path}"},
                },
            )
            return

        # 1. Authentication Check
        if not self._authenticate():
            logger.warning("Unauthenticated MCP HTTP request rejected")
            self._send_json_response(
                HTTPStatus.UNAUTHORIZED,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32001, "message": "Unauthorized: Invalid or missing API key"},
                },
            )
            return

        # 2. Content-Length Validation
        content_length_str = self.headers.get("Content-Length")
        if not content_length_str:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": INVALID_REQUEST, "message": "Missing Content-Length header"},
                },
            )
            return

        try:
            content_length = int(content_length_str)
        except ValueError:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": INVALID_REQUEST, "message": "Invalid Content-Length header"},
                },
            )
            return

        if content_length > MAX_CONTENT_LENGTH:
            self._send_json_response(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": INVALID_REQUEST, "message": "Request payload exceeds maximum allowed size"},
                },
            )
            return

        # 3. Read Body & Parse JSON
        try:
            raw_body = self.rfile.read(content_length)
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json_response(
                HTTPStatus.OK,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": PARSE_ERROR, "message": "Parse error: Invalid JSON payload"},
                },
            )
            return
        except Exception:
            self._send_json_response(
                HTTPStatus.BAD_REQUEST,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": INVALID_REQUEST, "message": "Failed to read request body"},
                },
            )
            return

        # 4. Dispatch to existing MCPServer.handle_request()
        try:
            response_data = self.server_instance.mcp_server.handle_request(payload)
            if response_data is None:
                # Notification or 204 No Content
                self.send_response(HTTPStatus.NO_CONTENT)
                self.end_headers()
                return

            self._send_json_response(HTTPStatus.OK, response_data)
        except Exception as e:
            logger.exception("Unexpected error in HTTP MCP request handler")
            self._send_json_response(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {
                    "jsonrpc": "2.0",
                    "id": payload.get("id") if isinstance(payload, dict) else None,
                    "error": {"code": INTERNAL_ERROR, "message": "Internal server error occurred"},
                },
            )


class HttpMCPServer:
    """
    Streamable HTTP Server adapter for Nasiko Sentinel MCP Server.
    
    Wraps MCPServer instance and provides an authenticated HTTP transport endpoint
    compatible with remote AI orchestrators and DronaHQ.
    """

    def __init__(
        self,
        settings: Settings,
        mcp_server: Optional[MCPServer] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.settings = settings
        self.mcp_server = mcp_server or MCPServer(settings)
        self.host = host or settings.mcp_http_host
        self.port = port or settings.mcp_http_port
        self.api_key = api_key or settings.sentinel_api_key

        # Fail safely if HTTP mode is configured without API key outside test
        if settings.environment != "test" and not self.api_key:
            raise ConfigError(
                "SENTINEL_API_KEY is required to start HttpMCPServer outside test environment",
                details={"host": self.host, "port": self.port},
            )

        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def server_address(self) -> Tuple[str, int]:
        if self._httpd:
            return self._httpd.server_address
        return (self.host, self.port)

    def start(self, threaded: bool = False) -> None:
        """Start the HTTP server on configured host and port."""
        if self._is_running:
            return

        self._httpd = ThreadingHTTPServer((self.host, self.port), MCPHTTPRequestHandler)
        # Store back-reference on server instance for request handler
        self._httpd.http_mcp_server = self  # type: ignore
        self._is_running = True

        actual_host, actual_port = self._httpd.server_address
        logger.info(f"Started HttpMCPServer on http://{actual_host}:{actual_port} (Auth enabled: {bool(self.api_key)})")

        if threaded:
            self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            self._thread.start()
        else:
            try:
                self._httpd.serve_forever()
            except KeyboardInterrupt:
                logger.info("HttpMCPServer shutting down on interrupt")
            finally:
                self.stop()

    def stop(self) -> None:
        """Gracefully stop the HTTP server."""
        if not self._is_running or not self._httpd:
            return

        self._is_running = False
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        except Exception as e:
            logger.debug(f"Error during HTTP server shutdown: {e}")
        finally:
            if self._thread and self._thread.is_alive() and threading.current_thread() != self._thread:
                self._thread.join(timeout=2.0)
            self._httpd = None
            self._thread = None
            logger.info("HttpMCPServer stopped")

