# TODO: Improve return value. Consider it's (un)necessity.


def register_foreman_api_resource(mcp, foreman_api):
    """Register the Foreman API as a resource with the MCP server."""

    @mcp.resource(
        name="Foreman API Resource",
        description="Checks if the Foreman API is available and can be used.",
        uri="foreman://api",
        mime_type="text/plain",
    )
    async def foreman_api_resource() -> str:
        try:
            foreman_api.call("ping", "ping", {})
            return "status: ok, msg: Foreman API is available"
        except Exception as e:
            return f"status: err, msg: Foreman API is not available, err: {str(e)}"
