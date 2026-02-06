# TODO: Improve metadata


from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context

from foreman_mcp_server.utils.utils import get_foreman_api


def register_foreman_api_resources(mcp, foreman_api):
    @mcp.resource(
        name="Foreman Resources",
        description="Provides a list of all resources available in the Foreman API.",
        uri="foreman://documentation/api/resources",
    )
    def foreman_api_resources(ctx: Context = CurrentContext()) -> str:
        api = foreman_api or get_foreman_api(ctx)
        resources = api.apidoc["docs"]["resources"].keys()
        return ", ".join(resources)
