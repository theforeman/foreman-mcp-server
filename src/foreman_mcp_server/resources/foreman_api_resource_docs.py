# TODO: Consider re-writing the cache into Markdown format.


from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from foreman_mcp_server.utils.utils import get_foreman_api


def register_foreman_api_resource_docs(mcp):
    @mcp.resource(
        name="Foreman API Resource Documentation",
        description="Returns the documentation of a specific Foreman API resource.",
        uri="foreman://documentation/api/{resource}",
        mime_type="text/plain",
    )
    def foreman_api_resource_docs(
        resource: str,
        ctx: Context = CurrentContext(),
    ) -> str:
        try:
            api = get_foreman_api(ctx)
            docs = api.apidoc["docs"]["resources"][resource]
            return f"{docs}"
        except Exception as e:
            return f"error: Failed to read API documentation for resource '{resource}': {str(e)}"
