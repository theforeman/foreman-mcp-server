import asyncio
from importlib.resources import files

import aiofiles
import httpx


def register_hammer_docs(mcp, _foreman_api, _get_context):
    """Register Hammer CLI documentation resource."""

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
        process = await asyncio.create_subprocess_exec(
            "hammer",
            "full-help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout.decode("utf-8")
        else:
            return f"error: Hammer CLI help command failed with error: {stderr.decode('utf-8')}"

    @mcp.resource(
        name="Hammer CLI Organization Info",
        description="Provides detailed information on actions and parameters within the `hammer organization` subcommand.",
        uri="hammer://organization-info",
        mime_type="text/markdown",
    )
    async def hammer_organization_info() -> str:
        try:
            data_path = files("foreman_mcp_server").joinpath(
                "data/hammer_organization_help.md"
            )
            async with aiofiles.open(data_path) as f:
                return await f.read()
        except FileNotFoundError:
            return "error: Hammer CLI organization help file not found."
        except Exception as e:
            return f"error: Failed to read Hammer CLI organization help: {str(e)}"
