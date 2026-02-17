import logging
import socket
from pathlib import Path

import apypie
import click
from fastmcp import FastMCP
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware
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


def parse_comma_separated_list(_ctx, _param, value):
    """Parse a comma-separated string into a list of stripped values."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


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
@click.option(
    "--port",
    default=8080,
    help="Port to listen on for HTTP",
    envvar="PORT",
    show_default=True,
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to listen on for HTTP",
    envvar="HOST",
    show_default=True,
)
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    callback=normalize_log_level,
    show_default=True,
)
@click.option(
    "--foreman-url",
    default=f"https://{socket.gethostname()}",
    help="Foreman URL to connect to",
    envvar="FOREMAN_URL",
    show_default=True,
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
    show_default=True,
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=True,
    is_flag=True,
    help="Verify SSL certificates when connecting to Foreman API.",
    show_default=True,
)
@click.option(
    "--ca-bundle",
    help="Path to CA certificate bundle file for SSL verification. If not specified, ./ca.pem will be used if it exists, otherwise system default CA bundle is used.",
    envvar="FOREMAN_CA_BUNDLE",
)
@click.option(
    "--allowed-rex-features",
    default="",
    help="Comma-separated list of allowed remote execution feature labels.",
    envvar="FOREMAN_ALLOWED_REX_FEATURES",
    show_default=True,
    callback=parse_comma_separated_list,
)
@click.option(
    "--allowed-cv-actions",
    help="Comma-separated list of allowed content view actions for the server to execute. If not specified, no actions are allowed."
    " "
    "Currently supported actions: incremental_update, publish, promote.",
    envvar="FOREMAN_ALLOWED_CV_ACTIONS",
    default="",
    show_default=True,
    callback=parse_comma_separated_list,
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
    ca_bundle: str,
    allowed_rex_features: list[str],
    allowed_cv_actions: list[str],
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

    # Resolve CA bundle path - check for ./ca.pem if none specified
    if ca_bundle is None:
        default_ca_path = Path.cwd() / "ca.pem"
        if default_ca_path.exists():
            ca_bundle = str(default_ca_path)

    # apypie expects certificate path as verify_ssl parameter, not ca_bundle
    if ca_bundle:
        verify_ssl = ca_bundle

    register_tools(mcp, allowed_rex_features, allowed_cv_actions)
    register_resources(mcp, allowed_rex_features)
    register_prompts(mcp)

    foreman_api = None
    if transport == "stdio":
        foreman_api = apypie.ForemanApi(
            uri=foreman_url,
            username=foreman_username,
            password=foreman_password,
            verify_ssl=verify_ssl,
        )
    mcp.add_middleware(ErrorHandlingMiddleware())
    mcp.add_middleware(AuthMiddleware(foreman_url, verify_ssl, foreman_api))
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
