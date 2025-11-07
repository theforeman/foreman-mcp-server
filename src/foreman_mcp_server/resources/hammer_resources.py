import asyncio
from importlib.resources import files

import aiofiles
import httpx

from ..tools.call_hammer_commands import (
    lifecycle_environment_create,
    lifecycle_environment_delete,
)

# Helpers
HAMMER_LIFECYCLE_ENVIRONMENT_LIST = "lifecycle-environment list"


def lifecycle_environment_info(
    organization_name: str, lifecycle_environment_name: str
) -> str:
    """Build hammer command for getting lifecycle environment info (without 'hammer' prefix)."""
    return f'lifecycle-environment info --organization "{organization_name}" --name "{lifecycle_environment_name}"'


async def execute_hammer_command_for_resource(command: str) -> str:
    process = await asyncio.create_subprocess_exec(
        "hammer",
        *command.split(),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        return stdout.decode("utf-8")
    else:
        return f"error: Hammer CLI command failed with error: {stderr.decode('utf-8')}"


# MCP resource registration
def register_hammer_resources(mcp):
    @mcp.resource(
        name="Hammer CLI Basic Information",
        description="Provides basic information about Hammer CLI, including usage and common commands.",
        uri="hammer://basic-information",
        mime_type="text/markdown",
    )
    async def hammer_basic_information() -> str:
        try:
            data_path = files("foreman_mcp_server").joinpath(
                "data/hammer_basic_information.md"
            )
            async with aiofiles.open(data_path) as f:
                return await f.read()
        except FileNotFoundError:
            return "error: Hammer CLI basic information file not found."
        except Exception as e:
            return f"error: Failed to read Hammer CLI basic information: {str(e)}"

    @mcp.resource(
        name="Hammer CLI Documentation Webpage",
        description="Provides access to Hammer CLI documentation from docs.theforeman.org. This resource contains information on nearly all Hammer CLI commands and their usage.",
        uri="hammer://web-documentation",
        mime_type="text/html",
    )
    async def hammer_web_documentation() -> str:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://docs.theforeman.org/nightly/Hammer_CLI/index-katello.html",
                    follow_redirects=True,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as e:
            return f"error: HTTP error {e.response.status_code} while fetching Hammer CLI documentation"
        except httpx.RequestError as e:
            return f"error: Request failed while fetching Hammer CLI documentation: {str(e)}"
        except Exception as e:
            return f"error: Failed to fetch Hammer CLI documentation: {str(e)}"

    @mcp.resource(
        name="Hammer CLI Full Help",
        description="Prints help for all available hammer commands, subcommands, and actions.",
        uri="hammer://full-help",
        mime_type="text/plain",
    )
    async def hammer_full_help() -> str:
        return await execute_hammer_command_for_resource("full-help")

    @mcp.resource(
        name="Hammer CLI Lifecycle Environment Info",
        description="Provides detailed information on actions and parameters within the `hammer lifecycle-environment` subcommand.",
        uri="hammer://lifecycle-environment-info",
        mime_type="text/markdown",
    )
    async def hammer_lifecycle_environment_info() -> str:
        try:
            data_path = files("foreman_mcp_server").joinpath(
                "data/hammer_lifecycle_environment_help.md"
            )
            async with aiofiles.open(data_path) as f:
                return await f.read()
        except FileNotFoundError:
            return "error: Hammer CLI lifecycle environment help file not found."
        except Exception as e:
            return (
                f"error: Failed to read Hammer CLI lifecycle environment help: {str(e)}"
            )

    @mcp.resource(
        name="Generate Hammer CLI Lifecycle Environment List",
        description="Generates a hammer command for listing lifecycle environments. Does not execute the command.",
        uri="hammer://generate-lifecycle-environment-list",
        mime_type="text/plain",
    )
    async def generate_hammer_lifecycle_environment_list() -> str:
        return f"hammer {HAMMER_LIFECYCLE_ENVIRONMENT_LIST}"

    @mcp.resource(
        name="Execute Hammer CLI Lifecycle Environment List",
        description="Executes the hammer command to list lifecycle environments and returns the output.",
        uri="hammer://execute-lifecycle-environment-list",
        mime_type="text/plain",
    )
    async def execute_hammer_lifecycle_environment_list() -> str:
        return await execute_hammer_command_for_resource(
            HAMMER_LIFECYCLE_ENVIRONMENT_LIST
        )

    @mcp.resource(
        name="Generate Hammer CLI Lifecycle Environment Info",
        description="Generates a hammer command for getting lifecycle environment information. Does not execute the command.",
        uri="hammer://generate-lifecycle-environment-info/{organization_name}/{lifecycle_environment_name}",
        mime_type="text/plain",
    )
    async def generate_hammer_lifecycle_environment_info(
        organization_name: str, lifecycle_environment_name: str
    ) -> str:
        return f"hammer {lifecycle_environment_info(organization_name, lifecycle_environment_name)}"

    @mcp.resource(
        name="Execute Hammer CLI Lifecycle Environment Info",
        description="Executes the hammer command to get lifecycle environment information and returns the output.",
        uri="hammer://execute-lifecycle-environment-info/{organization_name}/{lifecycle_environment_name}",
        mime_type="text/plain",
    )
    async def execute_hammer_lifecycle_environment_info(
        organization_name: str, lifecycle_environment_name: str
    ) -> str:
        return await execute_hammer_command_for_resource(
            lifecycle_environment_info(organization_name, lifecycle_environment_name)
        )

    @mcp.resource(
        name="Generate Hammer CLI Lifecycle Environment Create",
        description="Generates a hammer command for creating a lifecycle environment. Does not execute the command.",
        uri="hammer://generate-lifecycle-environment-create/{organization_name}/{lifecycle_environment_name}/{prior_lifecycle_environment_name}",
        mime_type="text/plain",
    )
    async def generate_hammer_lifecycle_environment_create(
        organization_name: str,
        lifecycle_environment_name: str,
        prior_lifecycle_environment_name: str,
    ) -> str:
        return f"hammer {lifecycle_environment_create(organization_name, lifecycle_environment_name, prior_lifecycle_environment_name)}"

    @mcp.resource(
        name="Generate Hammer CLI Lifecycle Environment Delete",
        description="Generates a hammer command for deleting a lifecycle environment. Does not execute the command.",
        uri="hammer://generate-lifecycle-environment-delete/{organization_name}/{lifecycle_environment_name}",
        mime_type="text/plain",
    )
    async def generate_hammer_lifecycle_environment_delete(
        organization_name: str,
        lifecycle_environment_name: str,
    ) -> str:
        return f"hammer {lifecycle_environment_delete(organization_name, lifecycle_environment_name)}"
