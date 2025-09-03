# TODO: Needs refactoring, better error handling or entire removal.

from apypie import ForemanApi
from apypie.resource import Resource
from fastmcp.exceptions import ToolError


async def assert_resource(
    to_check: str, resource_info: dict, get_context
) -> bool | None:
    """Checks if a specific resource is available in the resource list."""

    ctx = get_context()
    resource = await ctx.read_resource(
        f"foreman://documentation/{resource_info['type']}/{resource_info['list_name']}"
    )
    resources = resource[0].content.split(", ")
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


def mcp_info_headers(get_context) -> dict:
    """Returns MCP info headers for the request."""

    ctx = get_context()
    if ctx.request_context.request:
        return {
            "X-Foreman-MCP-Server-Host": f"{ctx.request_context.request.client.host}:{ctx.request_context.request.client.port}",
            "X-Foreman-MCP-Server-MCP-Session-ID": ctx.request_context.request.headers.get(
                "mcp-session-id"
            ),
        }
    else:
        return {}


def get_foreman_api(get_context) -> ForemanApi:
    """Retrieves the Foreman API instance for the given username."""

    ctx = get_context()
    foreman_username = ctx.request_context.request.headers.get("foreman_username")
    session_id = ctx.request_context.request.headers.get("mcp-session-id")
    user_map = getattr(ctx, "user_map", {})

    if foreman_username in user_map and session_id in user_map[foreman_username]:
        return user_map[foreman_username][session_id]
    raise RuntimeError(f"Foreman API is not available for {foreman_username}.")
