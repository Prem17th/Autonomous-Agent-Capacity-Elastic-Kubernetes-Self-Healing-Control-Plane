"""Application entrypoint for Nasiko Sentinel."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional, Sequence

# Ensure project root is in sys.path when running script directly
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src import __service_name__, __version__
from src.config.settings import Settings, get_settings
from src.errors.exceptions import ConfigError, SentinelError
from src.logger.logger import get_logger, log_event, setup_logging
from src.server.health import get_health_status
from src.server.http_server import HttpMCPServer
from src.server.mcp_server import MCPServer


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="nasiko-sentinel",
        description="Nasiko Sentinel - AI-powered elastic Kubernetes capacity and recovery system",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__service_name__} v{__version__}",
        help="Show program version and exit",
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Print current health and readiness status JSON and exit",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Print active sanitized configuration JSON and exit",
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Enable JSON-formatted log output",
    )
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument(
        "--stdio",
        action="store_true",
        help="Run MCP server over stdio transport (default)",
    )
    transport_group.add_argument(
        "--http",
        action="store_true",
        help="Run MCP server over Streamable HTTP transport",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main execution function."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = get_settings()
    except ConfigError as ce:
        sys.stderr.write(f"Configuration Error: {ce.message}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Initialization Error: {e}\n")
        return 1

    # Override transport if explicitly specified on CLI
    transport = settings.mcp_transport
    if args.http:
        transport = "http"
    elif args.stdio:
        transport = "stdio"

    # Initialize structured logging
    logger = setup_logging(
        log_level=settings.log_level,
        json_format=args.json_logs,
    )

    if args.health:
        health_info = get_health_status(settings)
        sys.stdout.write(json.dumps(health_info, indent=2) + "\n")
        return 0

    if args.config:
        config_info = settings.to_dict(safe=True)
        sys.stdout.write(json.dumps(config_info, indent=2) + "\n")
        return 0

    log_event(
        logger,
        20,  # INFO
        f"Starting {settings.app_name} v{settings.app_version}",
        {"environment": settings.environment, "transport": transport},
    )

    mcp_server = MCPServer(settings)

    if transport == "http":
        try:
            http_server = HttpMCPServer(settings, mcp_server=mcp_server)
            http_server.start(threaded=False)
        except ConfigError as ce:
            sys.stderr.write(f"Configuration Error: {ce.message}\n")
            return 1
    else:
        mcp_server.run_stdio()

    return 0


if __name__ == "__main__":
    sys.exit(main())

