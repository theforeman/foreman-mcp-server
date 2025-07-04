# TODO: Improve metadata


def register_foreman_api_resources(mcp, foreman_api):
    @mcp.resource(
        name="Foreman Resources",
        description="Provides a list of all resources available in the Foreman API.",
        uri="foreman://documentation/api/resources",
    )
    def foreman_api_resources() -> str:
        resources = foreman_api.apidoc["docs"]["resources"].keys()
        return ", ".join(resources)
