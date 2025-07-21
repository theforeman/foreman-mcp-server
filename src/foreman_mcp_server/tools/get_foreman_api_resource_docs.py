from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result
from ..utils.utils import assert_resource, get_foreman_api


def register_get_foreman_api_resource_docs(mcp, foreman_api, get_context):
    """Register a tool to get Foreman API resource documentation."""

    @mcp.tool(
        description="Fetches the documentation for a specific Foreman API resource.",
        tags=("foreman", "docs", "api", "resource", "cache"),
        annotations={
            "title": "Get Foreman API Resource Documentation",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def get_foreman_api_resource_docs(resource: str) -> ToolResult:
        try:
            api = foreman_api or get_foreman_api(get_context)
            await assert_resource(
                resource,
                {"name": "Resource", "list_name": "resources", "type": "api"},
                get_context,
            )
            docs = api.apidoc["docs"]["resources"][resource]
            message = (
                f"API documentation for resource '{resource}' fetched successfully"
            )
            return build_tool_result(
                {
                    "message": message,
                    "resource": resource,
                    "documentation": docs,
                }
            )
        except Exception as e:
            message = f"Failed to read API documentation for resource '{resource}'"
            return build_tool_result(
                {
                    "message": message,
                    "error": str(e),
                }
            )
