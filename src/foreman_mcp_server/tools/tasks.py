import asyncio
import json

from fastmcp.tools.tool import ToolResult
from requests.exceptions import HTTPError

from ..utils.content_utils import build_tool_result
from ..utils.utils import get_foreman_api, mcp_info_headers

# Terminal states for Foreman tasks
TASK_TERMINAL_STATES = ("stopped", "paused")

# Default polling configuration
DEFAULT_POLL_INTERVAL = 5  # seconds
DEFAULT_POLL_TIMEOUT = 300  # 5 minutes


def register_task_tools(mcp, foreman_api, get_context):
    @mcp.tool(
        description="Polls a Foreman task until it reaches a terminal state (stopped or paused). Returns the final task state. Supports background execution for long-running tasks.",
        tags=("foreman", "api", "get", "task", "polling"),
        annotations={
            "title": "Poll Task Until Completion",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def poll_task(
        task_id: str,
        timeout: int = DEFAULT_POLL_TIMEOUT,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> ToolResult:
        """
        Poll a Foreman task until it reaches a terminal state.

        Args:
            task_id: The UUID of the task to poll
            timeout: Maximum time to wait in seconds (default: 300)
            poll_interval: Time between polls in seconds (default: 5)
        """
        ctx = get_context()
        try:
            api = foreman_api or get_foreman_api(get_context)
            elapsed = 0

            # Always fetch task status at least once
            response = api.call(
                "foreman_tasks",
                "show",
                {"id": task_id},
                mcp_info_headers(get_context),
            )

            # Report initial progress based on task's progress field
            task_progress = response.get("progress", 0) or 0
            current_progress = int(task_progress * 100)
            await ctx.report_progress(
                current_progress, 100, f"Polling task {task_id}..."
            )

            while elapsed < timeout:
                state = response.get("state")
                if state in TASK_TERMINAL_STATES:
                    # Report 100% completion
                    await ctx.report_progress(
                        100, 100, f"Task completed with state: {state}"
                    )
                    return format_poll_success(response, elapsed)

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                response = api.call(
                    "foreman_tasks",
                    "show",
                    {"id": task_id},
                    mcp_info_headers(get_context),
                )

                # Report progress based on task's progress field
                task_progress = response.get("progress", 0) or 0
                new_progress = int(task_progress * 100)
                if new_progress > current_progress:
                    current_progress = new_progress

                message = f"Polling task {task_id}... ({elapsed}s elapsed, {current_progress}% complete)"
                await ctx.report_progress(current_progress, 100, message)

            # Check one final time after the loop exits
            state = response.get("state")
            if state in TASK_TERMINAL_STATES:
                await ctx.report_progress(
                    100, 100, f"Task completed with state: {state}"
                )
                return format_poll_success(response, elapsed)

            # Timeout reached
            await ctx.report_progress(
                current_progress, 100, f"Timeout reached after {timeout} seconds"
            )
            await ctx.info(f"Timeout reached after {timeout} seconds")
            return format_poll_timeout(task_id, timeout, response)
        except Exception as e:
            await ctx.info(f"Error: {e}")
            return format_poll_failure(task_id, e)


def format_poll_success(response: dict, elapsed: int) -> ToolResult:
    """Format a successful poll completion response."""
    structured_content = {
        "message": f"Task completed with state '{response.get('state')}' after {elapsed} seconds.",
        "task_id": response.get("id"),
        "state": response.get("state"),
        "result": response.get("result"),
        "started_at": response.get("started_at"),
        "ended_at": response.get("ended_at"),
        "duration": response.get("duration"),
        "progress": response.get("progress"),
        "humanized_result": response.get("humanized", {}).get("output")
        if response.get("humanized")
        else None,
    }
    return build_tool_result(structured_content)


def format_poll_timeout(task_id: str, timeout: int, last_response: dict) -> ToolResult:
    """Format a poll timeout response."""
    structured_content = {
        "message": f"Timeout reached after {timeout} seconds. Task is still running.",
        "task_id": task_id,
        "state": last_response.get("state"),
        "progress": last_response.get("progress"),
        "suggestion": "You can call poll_task again to continue waiting, or use call_foreman_api_get to check the task status manually.",
    }
    return build_tool_result(structured_content)


def format_poll_failure(task_id: str, exception: Exception) -> ToolResult:
    """Format a failed poll response."""
    structured_content = {
        "message": f"Failed to poll task '{task_id}'.",
        "error": str(exception),
    }
    if isinstance(exception, HTTPError):
        text = getattr(exception.response, "text", None)
        if text:
            try:
                structured_content["response"] = json.loads(text)
            except json.JSONDecodeError:
                structured_content["response"] = text
    return build_tool_result(structured_content)
