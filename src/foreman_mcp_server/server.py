import socket

import apypie
import click
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_context

from .prompts import register_prompts
from .resources import register_resources
from .tools import register_tools

# TODO: Revisit all the places to properly handle exceptions and errors. Consider using fastmcp's exceptions.


@click.command()
@click.option("--port", default=8080, help="Port to listen on for HTTP")
@click.option("--host", default="127.0.0.1", help="Host to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--foreman-url",
    default=f"https://{socket.gethostname()}",
    help="Foreman URL to connect to",
)
@click.option(
    "--foreman-username",
    default="admin",
    help="Username for Foreman API authentication",
)
@click.option(
    "--foreman-password",
    default="changeme",
    help="Password for Foreman API authentication",
)
@click.option(
    "--transport",
    default="streamable-http",
    help="Transport protocol to use (streamable-http, stdio)",
)
def main(
    host: str,
    port: int,
    log_level: str,
    foreman_url: str,
    foreman_username: str,
    foreman_password: str,
    transport: str,
) -> int:
    """Run the Foreman MCP server."""

    mcp = FastMCP(name="Foreman MCP Server")

    foreman_api = apypie.ForemanApi(
        uri=foreman_url,
        username=foreman_username,
        password=foreman_password,
        verify_ssl=False,
    )
    register_tools(mcp, foreman_api, get_context)
    register_resources(mcp, foreman_api, get_context)
    register_prompts(mcp, foreman_api, get_context)

    if transport == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(
            transport="streamable-http",
            host=host,
            port=port,
            log_level=log_level,
            show_banner=False,
        )

    return 0
