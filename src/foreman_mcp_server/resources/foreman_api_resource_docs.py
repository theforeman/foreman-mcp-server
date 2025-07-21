# TODO: Consider re-writing the cache into Markdown format.


from foreman_mcp_server.utils.utils import get_foreman_api


def register_foreman_api_resource_docs(mcp, foreman_api, get_context):
    @mcp.resource(
        name="Foreman API Resource Documentation",
        description="Returns the documentation of a specific Foreman API resource.",
        uri="foreman://documentation/api/{resource}",
        mime_type="text/plain",
    )
    def foreman_api_resource_docs(resource: str) -> str:
        try:
            api = foreman_api or get_foreman_api(get_context)
            docs = api.apidoc["docs"]["resources"][resource]
            return f"{docs}"
        except Exception as e:
            return f"error: Failed to read API documentation for resource '{resource}': {str(e)}"
