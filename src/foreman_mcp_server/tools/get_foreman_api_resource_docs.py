def register_get_foreman_api_resource_docs(mcp, foreman_api):
    """Register a tool to get Foreman API resource documentation."""

    @mcp.tool
    def get_foreman_api_resource_docs(resource: str) -> str:
        """Fetches the documentation for given Foreman API resource."""
        try:
            docs = foreman_api.apidoc["docs"]["resources"][resource]
            return f"{docs}"
        except Exception as e:
            return f"error: Failed to read API documentation for resource '{resource}': {str(e)}"
