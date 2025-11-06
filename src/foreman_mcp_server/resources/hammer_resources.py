from ..utils.hammer_utils import execute_hammer_command_for_resource


def register_hammer_resources(mcp):
    @mcp.resource(
        name="Hammer CLI Full Help",
        description="Prints help for all available hammer commands, subcommands, and actions.",
        uri="hammer://full-help",
        mime_type="text/plain",
    )
    async def hammer_full_help() -> str:
        return await execute_hammer_command_for_resource("full-help")
