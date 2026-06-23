# TODO: Needs refactoring, better error handling or entire removal.

from apypie import ForemanApi
from apypie.resource import Resource
from fastmcp import Context
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_request


async def assert_resource(
    to_check: str, resource_info: dict, ctx: Context
) -> bool | None:
    """Checks if a specific resource is available in the resource list."""

    resource = await ctx.read_resource(
        f"foreman://documentation/{resource_info['type']}/{resource_info['list_name']}"
    )
    resources = resource.contents[0].content.split(", ")
    if to_check not in resources:
        message = f"{resource_info['name']} '{to_check}' is not available in the list"
        raise ToolError(f"{message}: {', '.join(resources)}")
    else:
        return True


def assert_http_method(foreman_api, action_info: dict, http_method: str) -> bool | None:
    """Checks if the action uses provided HTTP method on the resource."""
    resource = Resource(foreman_api, action_info["resource"])
    action = resource.action(action_info["name"])
    route = action.find_route(action_info["params"])
    if route.method != http_method.lower():
        message = f"Action '{action_info['name']}' on resource '{action_info['resource']}' is not allowed"
        raise ToolError(
            f"{message}: {route.method.upper()} method is not allowed, expected {http_method.upper()}."
        )
    else:
        return True


def mcp_info_headers(_ctx: Context) -> dict:
    """Returns MCP info headers for the request."""

    try:
        request = get_http_request()
    except RuntimeError:
        return {}
    if request.client:
        return {
            "X-Foreman-MCP-Server-Host": f"{request.client.host}:{request.client.port}",
            "X-Foreman-MCP-Server-MCP-Session-ID": request.headers.get(
                "mcp-session-id"
            ),
        }
    return {}


def get_foreman_api(ctx: Context) -> ForemanApi:
    """Retrieves the Foreman API instance from the context.

    This function provides unified access to the ForemanApi instance across both
    stdio and streamable-http transports. AuthMiddleware stores foreman_api in
    _request_state, which child contexts inherit. The getattr fallback is a
    defensive safety net in case _request_state is absent in a future version.
    """
    request_state = getattr(ctx, "_request_state", None)
    foreman_api = (
        request_state.get("foreman_api") if request_state else None
    ) or getattr(ctx, "foreman_api", None)
    if foreman_api is not None:
        return foreman_api

    raise RuntimeError(
        "Foreman API is not available. Ensure the credentials were passed as CLI arguments in case of stdio transport or as http headers."
    )
