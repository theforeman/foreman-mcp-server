"""Task polling tool for long-running operations.

This tool provides a way to monitor Foreman/Katello async tasks
without requiring the AI to repeatedly call the API.
"""

import asyncio
from typing import Optional

from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result
from ..utils.utils import get_foreman_api, mcp_info_headers


def register_task_tools(mcp, foreman_api, get_context):
    """Register task monitoring tools with the MCP server."""

    @mcp.tool(
        description=(
            "Poll a Foreman/Katello task until completion or timeout. "
            "Use this to wait for async operations like remote execution jobs. "
            "Returns the final task state with summary information."
        ),
        tags=("foreman", "tasks", "monitoring", "remote"),
        annotations={
            "title": "Poll Task",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def poll_task(
        task_id: str,
        timeout_seconds: int = 300,
        poll_interval_seconds: int = 10,
    ) -> ToolResult:
        """Poll a task until it completes or times out.

        Args:
            task_id: The Foreman task UUID to monitor
            timeout_seconds: Maximum time to wait (default 300 = 5 minutes)
            poll_interval_seconds: Time between polls (default 10 seconds)

        Returns:
            Final task state with summary information.
        """
        try:
            api = foreman_api or get_foreman_api(get_context)
            headers = mcp_info_headers(get_context)

            elapsed = 0
            terminal_states = {"stopped", "paused"}

            while elapsed < timeout_seconds:
                task_response = api.call(
                    "foreman_tasks",
                    "show",
                    {"id": task_id},
                    headers,
                )

                state = task_response.get("state")
                result = task_response.get("result")

                if state in terminal_states:
                    return build_tool_result({
                        "success": True,
                        "completed": True,
                        "task": {
                            "id": task_id,
                            "state": state,
                            "result": result,
                            "started_at": task_response.get("started_at"),
                            "ended_at": task_response.get("ended_at"),
                            "duration": task_response.get("duration"),
                        },
                        "summary": _build_task_summary(task_response),
                        "message": f"Task completed with result: {result}",
                    })

                await asyncio.sleep(poll_interval_seconds)
                elapsed += poll_interval_seconds

            # Timeout - fetch final state
            task_response = api.call(
                "foreman_tasks",
                "show",
                {"id": task_id},
                headers,
            )

            return build_tool_result({
                "success": True,
                "completed": False,
                "timed_out": True,
                "task": {
                    "id": task_id,
                    "state": task_response.get("state"),
                    "result": task_response.get("result"),
                    "progress": task_response.get("progress"),
                    "started_at": task_response.get("started_at"),
                },
                "message": (
                    f"Task still running after {timeout_seconds} seconds. "
                    "You can call poll_task again to continue monitoring."
                ),
            })

        except Exception as e:
            return build_tool_result({
                "success": False,
                "error": str(e),
            })

    @mcp.tool(
        description=(
            "Get the current status of a Foreman/Katello task without waiting. "
            "Use this for a quick check on task progress."
        ),
        tags=("foreman", "tasks", "monitoring", "remote"),
        annotations={
            "title": "Get Task Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def get_task_status(task_id: str) -> ToolResult:
        """Get current status of a task without polling.

        Args:
            task_id: The Foreman task UUID to check

        Returns:
            Current task state and progress information.
        """
        try:
            api = foreman_api or get_foreman_api(get_context)
            headers = mcp_info_headers(get_context)

            task_response = api.call(
                "foreman_tasks",
                "show",
                {"id": task_id},
                headers,
            )

            terminal_states = {"stopped", "paused"}
            state = task_response.get("state")

            return build_tool_result({
                "success": True,
                "task": {
                    "id": task_id,
                    "state": state,
                    "result": task_response.get("result"),
                    "progress": task_response.get("progress"),
                    "started_at": task_response.get("started_at"),
                    "ended_at": task_response.get("ended_at"),
                    "duration": task_response.get("duration"),
                    "action": task_response.get("action"),
                },
                "is_complete": state in terminal_states,
                "summary": _build_task_summary(task_response) if state in terminal_states else None,
            })

        except Exception as e:
            return build_tool_result({
                "success": False,
                "error": str(e),
            })


def _build_task_summary(task_response: dict) -> dict:
    """Build a summary of task execution results."""
    output = task_response.get("output", {})
    humanized = task_response.get("humanized", {})

    return {
        "action": task_response.get("action"),
        "result": task_response.get("result"),
        "duration": task_response.get("duration"),
        "output": output if isinstance(output, dict) else {},
        "humanized_output": humanized.get("output") if humanized else None,
        "errors": humanized.get("errors") if humanized else None,
    }
