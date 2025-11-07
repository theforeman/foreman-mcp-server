"""Shared utilities for Hammer CLI integration."""

import asyncio
import os
import shlex


# Command builders - return hammer commands without 'hammer' prefix
def organization_list_command() -> str:
    """Build hammer command for listing organizations."""
    return "organization list"


def organization_info_command(name: str) -> str:
    """
    Build hammer command for getting organization info.

    Args:
        name: Organization name
    """
    return f'organization info --name "{name}"'


def get_user_credentials(get_context, foreman_api=None):
    """
    Extract user credentials from MCP context.

    In streamable-http mode: Extracts credentials from request headers
    In stdio mode: Returns None (uses ~/.hammer/cli_config.yml)

    Args:
        get_context: FastMCP context getter function
        foreman_api: Optional ForemanApi instance to get URL from

    Returns:
        tuple: (username, password, foreman_url) or (None, None, None)
    """
    try:
        ctx = get_context()
        if ctx.request_context.request:
            # Streamable-HTTP mode: get credentials from headers
            username = ctx.request_context.request.headers.get("foreman_username")
            password = ctx.request_context.request.headers.get("foreman_token")

            # Get foreman_url from the foreman_api instance
            foreman_url = None
            if foreman_api:
                foreman_url = foreman_api.uri
            else:
                # Try to get from middleware
                from .utils import get_foreman_api

                try:
                    api_instance = get_foreman_api(get_context)
                    if api_instance:
                        foreman_url = api_instance.uri
                except Exception:
                    pass

            return (username, password, foreman_url)
    except Exception:
        pass

    # Stdio mode or no context: return None to use default config
    return (None, None, None)


async def execute_hammer_command(
    command: str, username: str = None, password: str = None, foreman_url: str = None
):
    """
    Execute a hammer CLI command with credentials.

    Args:
        command: The hammer command to execute (without 'hammer' prefix)
        username: Foreman username (optional)
        password: Foreman password (optional)
        foreman_url: Foreman URL (optional)

    Returns:
        tuple: (success: bool, output: str, error: str = None, returncode: int)
        - On success: (True, stdout_text, returncode)
        - On failure: (False, stdout_text, stderr_text, returncode)
    """
    # Build environment with user-specific credentials
    env = os.environ.copy()

    # Set credentials via environment variables if provided
    if username:
        env["FOREMAN_USERNAME"] = username
    if password:
        env["FOREMAN_PASSWORD"] = password
    if foreman_url:
        env["FOREMAN_URL"] = foreman_url

    # Execute hammer command with stdin redirected to /dev/null
    # This prevents interactive password prompts
    process = await asyncio.create_subprocess_exec(
        "hammer",
        *shlex.split(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.DEVNULL,  # Prevent interactive prompts
        env=env,
    )
    stdout, stderr = await process.communicate()

    # Decode output
    stdout_text = stdout.decode("utf-8") if stdout else ""
    stderr_text = stderr.decode("utf-8") if stderr else ""

    if process.returncode == 0:
        return (True, stdout_text, process.returncode)
    else:
        return (False, stdout_text, stderr_text, process.returncode)
