from fastmcp.tools.tool import ToolResult
from mcp.types import TextContent

from ..utils.utils import assert_resource


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
            await assert_resource(
                resource,
                {"name": "Resource", "list_name": "resources", "type": "api"},
                get_context,
            )
            docs = foreman_api.apidoc["docs"]["resources"][resource]
            message = (
                f"API documentation for resource '{resource}' fetched successfully"
            )
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {docs}")],
                structured_content={
                    "message": message,
                    "resource": resource,
                    "documentation": docs,
                },
            )
        except Exception as e:
            message = f"Failed to read API documentation for resource '{resource}'"
            return ToolResult(
                content=[TextContent(type="text", text=f"{message}: {str(e)}")],
                structured_content={"message": message, "error": str(e)},
            )
