# TODO: Needs refactoring, better error handling or entire removal.

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
