"""Model Context Protocol (MCP) Server for Nasiko Sentinel."""

import json
import sys
from typing import Any, Callable, Dict, List, Optional

from src.autoscaler.policy import RecoveryPolicyEngine
from src.autoscaler.provider import AutoscalerProvider
from src.autoscaler.simulated_provider import SimulatedAutoscalerProvider
from src.bedrock.bedrock_reasoner import BedrockRuntimeReasoner
from src.bedrock.mock_reasoner import MockBedrockReasoner
from src.bedrock.orchestrator import SentinelRecoveryReasoner
from src.config.settings import Settings
from src.errors.exceptions import InfrastructureError, SentinelError, ValidationError
from src.kubernetes.adapter import KubernetesAdapter
from src.kubernetes.client import KubernetesClient
from src.logger.logger import get_logger, log_event
from src.server.health import get_health_status
from src.tools import (
    AGENT_STATUS_DESC,
    AGENT_STATUS_NAME,
    AGENT_STATUS_SCHEMA,
    AUTOSCALER_STATUS_DESC,
    AUTOSCALER_STATUS_NAME,
    AUTOSCALER_STATUS_SCHEMA,
    DIAGNOSIS_DESC,
    DIAGNOSIS_NAME,
    DIAGNOSIS_SCHEMA,
    NODE_CAPACITY_DESC,
    NODE_CAPACITY_NAME,
    NODE_CAPACITY_SCHEMA,
    NODE_POOL_STATUS_DESC,
    NODE_POOL_STATUS_NAME,
    NODE_POOL_STATUS_SCHEMA,
    PENDING_PODS_DESC,
    PENDING_PODS_NAME,
    PENDING_PODS_SCHEMA,
    POD_EVENTS_DESC,
    POD_EVENTS_NAME,
    POD_EVENTS_SCHEMA,
    REASON_RECOVERY_DESC,
    REASON_RECOVERY_NAME,
    REASON_RECOVERY_SCHEMA,
    RECOVERY_STATUS_DESC,
    RECOVERY_STATUS_NAME,
    RECOVERY_STATUS_SCHEMA,
    REQUEST_SCALE_UP_DESC,
    REQUEST_SCALE_UP_NAME,
    REQUEST_SCALE_UP_SCHEMA,
    RETRY_AGENT_DESC,
    RETRY_AGENT_NAME,
    RETRY_AGENT_SCHEMA,
    VERIFY_RECOVERY_DESC,
    VERIFY_RECOVERY_NAME,
    VERIFY_RECOVERY_SCHEMA,
    WAIT_FOR_CAPACITY_DESC,
    WAIT_FOR_CAPACITY_NAME,
    WAIT_FOR_CAPACITY_SCHEMA,
    handle_diagnose_capacity,
    handle_get_agent_status,
    handle_get_autoscaler_status,
    handle_get_node_capacity,
    handle_get_node_pool_status,
    handle_get_pending_pods,
    handle_get_pod_events,
    handle_get_recovery_status,
    handle_reason_recovery,
    handle_request_scale_up,
    handle_retry_agent,
    handle_verify_agent_recovery,
    handle_wait_for_capacity,
)

logger = get_logger("server")

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


class MCPServer:
    """
    Model Context Protocol (MCP) server for Nasiko Sentinel.
    
    Exposes verified Kubernetes observation, capacity diagnosis,
    controlled autoscaling/recovery, and AWS Bedrock AI reasoning tools over JSON-RPC 2.0.
    """

    def __init__(
        self,
        settings: Settings,
        adapter: Optional[KubernetesAdapter] = None,
        autoscaler_provider: Optional[AutoscalerProvider] = None,
        policy_engine: Optional[RecoveryPolicyEngine] = None,
        reasoner: Optional[SentinelRecoveryReasoner] = None,
    ) -> None:
        self.settings = settings
        if adapter is None:
            client = KubernetesClient(settings)
            self.adapter = KubernetesAdapter(client)
        else:
            self.adapter = adapter

        if autoscaler_provider is None:
            self.autoscaler_provider = SimulatedAutoscalerProvider(adapter=self.adapter)
        else:
            self.autoscaler_provider = autoscaler_provider

        if policy_engine is None:
            self.policy_engine = RecoveryPolicyEngine()
        else:
            self.policy_engine = policy_engine

        if reasoner is None:
            if settings.bedrock_mock_mode:
                primary = MockBedrockReasoner(
                    model_id=settings.bedrock_model_id or "mock-bedrock-model"
                )
            else:
                primary = BedrockRuntimeReasoner(settings)
            self.reasoner = SentinelRecoveryReasoner(primary_reasoner=primary)
        else:
            self.reasoner = reasoner

        self.tools: Dict[str, Dict[str, Any]] = {}
        self.tool_handlers: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self.is_running = False
        self._register_default_tools()

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Register a new tool in the MCP registry."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self.tool_handlers[name] = handler
        logger.debug(f"Registered MCP tool: {name}")

    def _register_default_tools(self) -> None:
        """Register Phase 1, Phase 2, Phase 3, and Phase 4 tools."""
        # 1. Health Status Tool
        self.register_tool(
            name="get_health",
            description="Returns current service health, environment, phase status, and dependency readiness.",
            input_schema={"type": "object", "properties": {}},
            handler=lambda args: get_health_status(
                self.settings,
                k8s_connected=self.adapter.check_connection(),
                autoscaler_type=self.autoscaler_provider.provider_type,
                reasoner_name=self.reasoner.primary_reasoner.reasoner_name if self.reasoner.primary_reasoner else "deterministic_fallback",
            ),
        )

        # 2. Phase 2 Kubernetes Observation & Diagnosis Tools (Active)
        self.register_tool(
            name=AGENT_STATUS_NAME,
            description=AGENT_STATUS_DESC,
            input_schema=AGENT_STATUS_SCHEMA,
            handler=lambda args: handle_get_agent_status(self.adapter, args),
        )

        self.register_tool(
            name=PENDING_PODS_NAME,
            description=PENDING_PODS_DESC,
            input_schema=PENDING_PODS_SCHEMA,
            handler=lambda args: handle_get_pending_pods(self.adapter, args),
        )

        self.register_tool(
            name=POD_EVENTS_NAME,
            description=POD_EVENTS_DESC,
            input_schema=POD_EVENTS_SCHEMA,
            handler=lambda args: handle_get_pod_events(self.adapter, args),
        )

        self.register_tool(
            name=NODE_CAPACITY_NAME,
            description=NODE_CAPACITY_DESC,
            input_schema=NODE_CAPACITY_SCHEMA,
            handler=lambda args: handle_get_node_capacity(self.adapter, args),
        )

        self.register_tool(
            name=DIAGNOSIS_NAME,
            description=DIAGNOSIS_DESC,
            input_schema=DIAGNOSIS_SCHEMA,
            handler=lambda args: handle_diagnose_capacity(self.adapter, args),
        )

        # 3. Phase 3 Controlled Autoscaling & Recovery Tools (Active)
        self.register_tool(
            name=REQUEST_SCALE_UP_NAME,
            description=REQUEST_SCALE_UP_DESC,
            input_schema=REQUEST_SCALE_UP_SCHEMA,
            handler=lambda args: handle_request_scale_up(
                self.adapter,
                self.autoscaler_provider,
                self.policy_engine,
                args,
            ),
        )

        self.register_tool(
            name=WAIT_FOR_CAPACITY_NAME,
            description=WAIT_FOR_CAPACITY_DESC,
            input_schema=WAIT_FOR_CAPACITY_SCHEMA,
            handler=lambda args: handle_wait_for_capacity(
                self.autoscaler_provider,
                args,
            ),
        )

        self.register_tool(
            name=AUTOSCALER_STATUS_NAME,
            description=AUTOSCALER_STATUS_DESC,
            input_schema=AUTOSCALER_STATUS_SCHEMA,
            handler=lambda args: handle_get_autoscaler_status(
                self.autoscaler_provider,
                args,
            ),
        )

        self.register_tool(
            name=NODE_POOL_STATUS_NAME,
            description=NODE_POOL_STATUS_DESC,
            input_schema=NODE_POOL_STATUS_SCHEMA,
            handler=lambda args: handle_get_node_pool_status(
                self.autoscaler_provider,
                args,
            ),
        )

        self.register_tool(
            name=RECOVERY_STATUS_NAME,
            description=RECOVERY_STATUS_DESC,
            input_schema=RECOVERY_STATUS_SCHEMA,
            handler=lambda args: handle_get_recovery_status(args),
        )

        self.register_tool(
            name=VERIFY_RECOVERY_NAME,
            description=VERIFY_RECOVERY_DESC,
            input_schema=VERIFY_RECOVERY_SCHEMA,
            handler=lambda args: handle_verify_agent_recovery(
                self.adapter,
                args,
            ),
        )

        self.register_tool(
            name=RETRY_AGENT_NAME,
            description=RETRY_AGENT_DESC,
            input_schema=RETRY_AGENT_SCHEMA,
            handler=lambda args: handle_retry_agent(
                self.adapter,
                args,
            ),
        )

        # 4. Phase 4 AI Reasoning Tool (Active)
        self.register_tool(
            name=REASON_RECOVERY_NAME,
            description=REASON_RECOVERY_DESC,
            input_schema=REASON_RECOVERY_SCHEMA,
            handler=lambda args: handle_reason_recovery(
                self.adapter,
                self.autoscaler_provider,
                self.reasoner,
                args,
            ),
        )

    def handle_request(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC 2.0 request."""
        if not isinstance(request_data, dict):
            return self._make_error_response(None, INVALID_REQUEST, "Invalid JSON-RPC Request object")

        req_id = request_data.get("id")
        method = request_data.get("method")
        params = request_data.get("params", {})

        if not method or not isinstance(method, str):
            return self._make_error_response(req_id, INVALID_REQUEST, "Missing or invalid 'method' field")

        logger.debug(f"Handling JSON-RPC method: {method}", extra={"event_data": {"id": req_id, "method": method}})

        try:
            if method == "initialize":
                return self._handle_initialize(req_id, params)
            elif method == "notifications/initialized":
                return None
            elif method == "ping":
                return self._make_success_response(req_id, {})
            elif method == "tools/list":
                return self._handle_tools_list(req_id)
            elif method == "tools/call":
                return self._handle_tools_call(req_id, params)
            else:
                return self._make_error_response(req_id, METHOD_NOT_FOUND, f"Method not found: {method}")
        except SentinelError as se:
            logger.error(f"Sentinel error processing {method}: {se}")
            return self._make_error_response(req_id, INTERNAL_ERROR, se.message, data=se.to_dict())
        except Exception as e:
            logger.exception(f"Unexpected error processing {method}: {e}")
            return self._make_error_response(req_id, INTERNAL_ERROR, f"Internal error: {str(e)}")

    def _handle_initialize(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._make_success_response(
            req_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": self.settings.app_name,
                    "version": self.settings.app_version,
                },
            },
        )

    def _handle_tools_list(self, req_id: Any) -> Dict[str, Any]:
        return self._make_success_response(req_id, {"tools": list(self.tools.values())})

    def _handle_tools_call(self, req_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(params, dict):
            return self._make_error_response(req_id, INVALID_PARAMS, "Parameters must be an object")

        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(arguments, dict):
            arguments = {}

        if not tool_name or tool_name not in self.tool_handlers:
            return self._make_error_response(req_id, INVALID_PARAMS, f"Tool '{tool_name}' is not registered")

        handler = self.tool_handlers[tool_name]
        try:
            result = handler(arguments)
            return self._make_success_response(
                req_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ]
                },
            )
        except ValidationError as ve:
            logger.warning(f"Tool validation error in {tool_name}: {ve.message}")
            return self._make_error_response(req_id, INVALID_PARAMS, ve.message, data=ve.to_dict())
        except InfrastructureError as ie:
            logger.error(f"Tool infrastructure error in {tool_name}: {ie.message}")
            return self._make_error_response(req_id, INTERNAL_ERROR, ie.message, data=ie.to_dict())
        except Exception as e:
            logger.exception(f"Unexpected error executing {tool_name}: {e}")
            return self._make_error_response(req_id, INTERNAL_ERROR, f"Error executing tool '{tool_name}': {e}")

    def _make_success_response(self, req_id: Any, result: Any) -> Dict[str, Any]:
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _make_error_response(
        self,
        req_id: Any,
        code: int,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        err_body: Dict[str, Any] = {"code": code, "message": message}
        if data is not None:
            err_body["data"] = data
        return {"jsonrpc": "2.0", "id": req_id, "error": err_body}

    def run_stdio(self) -> None:
        """Run MCP server over stdio transport."""
        self.is_running = True
        log_event(
            logger,
            20,  # INFO
            "Starting Nasiko Sentinel MCP Server (stdio transport)",
            {
                "service": self.settings.app_name,
                "version": self.settings.app_version,
                "environment": self.settings.environment,
                "phase": 4,
            },
        )

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request_data = json.loads(line)
                except json.JSONDecodeError as e:
                    error_resp = self._make_error_response(
                        None, PARSE_ERROR, f"Invalid JSON received: {e}"
                    )
                    sys.stdout.write(json.dumps(error_resp) + "\n")
                    sys.stdout.flush()
                    continue

                response = self.handle_request(request_data)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Server received interrupt signal, shutting down.")
        finally:
            self.is_running = False
            logger.info("Nasiko Sentinel MCP Server stopped.")
