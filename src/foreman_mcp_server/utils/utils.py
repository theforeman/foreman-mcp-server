# TODO: Needs refactoring, better error handling or entire removal.

from apypie import ForemanApi
from apypie.resource import Resource
from fastmcp import Context
from fastmcp.exceptions import ToolError


async def assert_resource(
    to_check: str, resource_info: dict, ctx: Context
) -> bool | None:
    """Checks if a specific resource is available in the resource list."""

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


def mcp_info_headers(ctx: Context) -> dict:
    """Returns MCP info headers for the request."""

    if ctx.request_context.request:
        return {
            "X-Foreman-MCP-Server-Host": f"{ctx.request_context.request.client.host}:{ctx.request_context.request.client.port}",
            "X-Foreman-MCP-Server-MCP-Session-ID": ctx.request_context.request.headers.get(
                "mcp-session-id"
            ),
        }
    else:
        return {}


def get_foreman_api(ctx: Context) -> ForemanApi:
    """Retrieves the Foreman API instance from the context.

    This function provides unified access to the ForemanApi instance across
    both stdio and streamable-http transports:

    - For stdio transport: StdioAuthMiddleware injects `foreman_api` directly
      into the context at startup.
    - For streamable-http transport: AuthMiddleware creates and caches API
      instances per user/session in `user_map`, accessed via HTTP headers.
    """
    # Check for direct foreman_api attribute (stdio transport via StdioAuthMiddleware)
    foreman_api = getattr(ctx, "foreman_api", None)
    if foreman_api is not None:
        return foreman_api

    # Fall back to user_map lookup (streamable-http transport via AuthMiddleware)
    user_map = getattr(ctx, "user_map", {})
    if user_map and ctx.request_context and ctx.request_context.request:
        foreman_username = ctx.request_context.request.headers.get("foreman_username")
        session_id = ctx.request_context.request.headers.get("mcp-session-id")
        if foreman_username in user_map and session_id in user_map[foreman_username]:
            return user_map[foreman_username][session_id]

    raise RuntimeError(
        "Foreman API is not available. Ensure the appropriate middleware is configured."
    )
