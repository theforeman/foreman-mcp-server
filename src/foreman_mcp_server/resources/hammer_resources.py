from ..utils.hammer_utils import (
    execute_hammer_command,
    get_user_credentials,
    organization_info_command,
    organization_list_command,
)


def register_hammer_resources(mcp, foreman_api, get_context):
    """Register Hammer CLI resources for read-only operations."""

    # Generate resources - return command strings without executing
    @mcp.resource(
        name="Generate Hammer Organization List Command",
        description="Generates a hammer command for listing organizations. Does not execute the command.",
        uri="hammer://generate-organization-list",
        mime_type="text/plain",
    )
    async def generate_hammer_organization_list() -> str:
        """Returns the hammer command string for listing organizations."""
        return f"hammer {organization_list_command()}"

    @mcp.resource(
        name="Generate Hammer Organization Info Command",
        description="Generates a hammer command for getting organization information. Does not execute the command.",
        uri="hammer://generate-organization-info/{name}",
        mime_type="text/plain",
    )
    async def generate_hammer_organization_info(name: str) -> str:
        """
        Returns the hammer command string for getting organization info.

        Args:
            name: Organization name
        """
        return f"hammer {organization_info_command(name)}"

    # Execute resources - run commands and return output
    @mcp.resource(
        name="Execute Hammer Organization List",
        description="Executes the hammer command to list all organizations and returns the output. "
        "Supports multi-user: in streamable-http mode uses per-user credentials from headers, "
        "in stdio mode uses credentials from ~/.hammer/cli_config.yml or startup args.",
        uri="hammer://execute-organization-list",
        mime_type="text/plain",
    )
    async def execute_hammer_organization_list() -> str:
        """Returns list of all organizations."""
        username, password, foreman_url = get_user_credentials(get_context, foreman_api)
        command = organization_list_command()
        success, output, *rest = await execute_hammer_command(
            command, username, password, foreman_url
        )
        if success:
            return output
        else:
            error = rest[0] if rest else ""
            return f"Error executing command 'hammer {command}':\n{error}"

    @mcp.resource(
        name="Execute Hammer Organization Info",
        description="Executes the hammer command to get detailed organization information and returns the output. "
        "Provides complete details including name, label, description, users, smart proxies, "
        "subnets, compute resources, media, templates, domains, environments, locations, and "
        "parameters. Supports multi-user: in streamable-http mode uses per-user credentials "
        "from headers, in stdio mode uses credentials from ~/.hammer/cli_config.yml or startup args.",
        uri="hammer://execute-organization-info/{name}",
        mime_type="text/plain",
    )
    async def execute_hammer_organization_info(name: str) -> str:
        """
        Returns detailed information about an organization.

        Args:
            name: Organization name
        """
        username, password, foreman_url = get_user_credentials(get_context, foreman_api)
        command = organization_info_command(name)
        success, output, *rest = await execute_hammer_command(
            command, username, password, foreman_url
        )
        if success:
            return output
        else:
            error = rest[0] if rest else ""
            return f"Error executing command 'hammer {command}':\n{error}"
