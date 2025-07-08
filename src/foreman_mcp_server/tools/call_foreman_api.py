from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..utils.utils import assert_resource


# TODO: Probably split it into multiple tools (read-only, destructive, etc)
def register_call_foreman_api(mcp, foreman_api, get_context):
    @mcp.tool(
        description="Calls an action on a Foreman API resource.",
        tags=("foreman", "api", "action", "resource", "remote"),
        annotations={
            "title": "Call Foreman API Action",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def call_foreman_api(resource: str, action: str, params: dict) -> ToolResult:
        try:
            await assert_resource(
                resource,
                {"name": "Resource", "list_name": "resources", "type": "api"},
                get_context,
            )
            response = foreman_api.call(resource, action, params)
            message = (
                f"Action '{action}' on resource '{resource}' executed successfully."
            )
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {response}")],
                structured_content={"message": message, "response": response},
            )
        except Exception as e:
            message = f"Failed to execute action '{action}' on resource '{resource}'"
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {str(e)}")],
                structured_content={"message": message, "error": str(e)},
            )
