import logging
import socket

import apypie
import click
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_context
from fastmcp.settings import LOG_LEVEL
from fastmcp.utilities.logging import configure_logging

from .middleware.auth import AuthMiddleware
from .middleware.logging import LoggingMiddleware
from .prompts import register_prompts
from .resources import register_resources
from .tools import register_tools

# TODO: Revisit all the places to properly handle exceptions and errors. Consider using fastmcp's exceptions.


def normalize_log_level(_ctx, _param, value):
    """Standardize log level input to uppercase."""
    if value:
        value = value.upper()
    return value


def assert_server_mode(foreman_username: str, foreman_password: str, transport: str):
    """Assert that the server is running in the correct mode."""
    if transport == "streamable-http":
        if foreman_username or foreman_password:
            raise ValueError(
                "Foreman username and password should not be set when using streamable-http transport."
            )
    else:
        if not foreman_username or not foreman_password:
            raise ValueError(
                "Foreman username and password must be set when using stdio transport."
            )


@click.command()
@click.option("--port", default=8080, help="Port to listen on for HTTP")
@click.option("--host", default="127.0.0.1", help="Host to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    callback=normalize_log_level,
)
@click.option(
    "--foreman-url",
    default=f"https://{socket.gethostname()}",
    help="Foreman URL to connect to",
)
@click.option(
    "--foreman-username",
    help="Username for Foreman API authentication. Can be set via FOREMAN_USERNAME environment variable.",
    envvar="FOREMAN_USERNAME",
)
@click.option(
    "--foreman-password",
    help="Password for Foreman API authentication. Can be set via FOREMAN_PASSWORD environment variable. Personal access tokens are recommended.",
    envvar="FOREMAN_PASSWORD",
)
@click.option(
    "--transport",
    default="streamable-http",
    help="Transport protocol to use (streamable-http, stdio)",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=True,
    is_flag=True,
    help="Verify SSL certificates when connecting to Foreman API.",
)
@click.pass_context
def main(
    ctx: click.Context,
    host: str,
    port: int,
    log_level: LOG_LEVEL,
    foreman_url: str,
    foreman_username: str,
    foreman_password: str,
    transport: str,
    verify_ssl: bool,
) -> int:
    """Run the Foreman MCP server."""

    # Default loggers
    logging.basicConfig(level=log_level)
    configure_logging(level=log_level)
    # Global logger for the MCP server
    logger = logging.getLogger("foreman_mcp_server")
    logger.setLevel(log_level)
    try:
        assert_server_mode(foreman_username, foreman_password, transport)
    except ValueError as e:
        logger.error(f"configuration: {e}")
        ctx.exit(1)

    mcp = FastMCP(name="Foreman MCP Server")

    foreman_api = None
    if transport == "stdio":
        foreman_api = apypie.ForemanApi(
            uri=foreman_url,
            username=foreman_username,
            password=foreman_password,
            verify_ssl=verify_ssl,
        )
    register_tools(mcp, foreman_api, get_context)
    register_resources(mcp, foreman_api, get_context)
    register_prompts(mcp, foreman_api, get_context)

    # TODO: We should've probably used https://gofastmcp.com/servers/middleware#error-handling-middleware for error handling
    if transport == "streamable-http":
        mcp.add_middleware(AuthMiddleware(foreman_url, verify_ssl))
    mcp.add_middleware(LoggingMiddleware())

    if transport == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            show_banner=False,
            log_level=log_level,
        )

    ctx.exit(0)
