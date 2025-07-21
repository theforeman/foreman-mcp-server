# TODO: Improve metadata


from foreman_mcp_server.utils.utils import get_foreman_api


def register_foreman_api_resources(mcp, foreman_api, get_context):
    @mcp.resource(
        name="Foreman Resources",
        description="Provides a list of all resources available in the Foreman API.",
        uri="foreman://documentation/api/resources",
    )
    def foreman_api_resources() -> str:
        api = foreman_api or get_foreman_api(get_context)
        resources = api.apidoc["docs"]["resources"].keys()
        return ", ".join(resources)
