import json
from collections.abc import Callable, Sequence

import apypie
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
from requests.exceptions import HTTPError

from ..utils.content_utils import build_tool_result
from ..utils.utils import get_foreman_api, mcp_info_headers


def register_remote_execution_tools(
    mcp: FastMCP,
    foreman_api: apypie.ForemanApi | None,
    get_context: Callable,
    allowed_rex_features: Sequence[str] = (),
) -> None:
    @mcp.tool(
        description="""Triggers a remote execution job on Foreman using a remote execution feature.

Before using this tool, the agent should:
1. Use call_foreman_api_get to list remote execution features (resource: "remote_execution_features", action: "index")
2. Pick the appropriate feature for the task
3. Use call_foreman_api_get to read the feature's associated job template (resource: "job_templates", action: "show", params: {"id": <job_template_id from feature>}) to see what inputs it accepts
4. Call this tool with the feature label and appropriate inputs

Returns the job invocation ID and task ID for polling.""",
        tags=("foreman", "api", "post", "remote-execution", "job"),
        annotations={
            "title": "Trigger Remote Execution Job",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def trigger_remote_execution_job(
        feature: str,
        search_query: str,
        inputs: dict | None = None,
        description: str | None = None,
    ) -> ToolResult:
        """
        Trigger a remote execution job on target hosts using a remote execution feature.

        Args:
            feature: The remote execution feature label (e.g., "katello_errata_install")
            search_query: Host search query (e.g., "installable_errata = RHSA-2025:1234")
            inputs: Optional dictionary of template inputs (varies by template)
            description: Optional description for the job invocation
        """
        # Validate feature against allowlist
        if feature not in allowed_rex_features:
            raise ToolError(
                f"Feature '{feature}' is not allowed. "
                f"Allowed features: {', '.join(allowed_rex_features)}"
            )

        try:
            api = foreman_api or get_foreman_api(get_context)

            # Build the job invocation payload
            job_invocation_params = {
                "job_invocation": {
                    "feature": feature,
                    "targeting_type": "static_query",
                    "search_query": search_query,
                }
            }

            if inputs:
                job_invocation_params["job_invocation"]["inputs"] = inputs

            if description:
                job_invocation_params["job_invocation"]["description"] = description

            response = api.call(
                "job_invocations",
                "create",
                job_invocation_params,
                mcp_info_headers(get_context),
            )

            return format_job_invocation_success(response)
        except Exception as e:
            return format_job_invocation_failure(e)


def format_job_invocation_success(response: dict) -> ToolResult:
    """Format a successful job invocation response."""
    structured_content = {
        "message": "Remote execution job triggered successfully.",
        "job_invocation_id": response.get("id"),
        "task_id": response.get("task", {}).get("id") if response.get("task") else None,
        "description": response.get("description"),
        "status": response.get("status"),
        "status_label": response.get("status_label"),
        "targeting": {
            "search_query": response.get("targeting", {}).get("search_query"),
            "hosts_count": response.get("total_hosts_count"),
        },
    }
    return build_tool_result(structured_content)


def format_job_invocation_failure(exception: Exception) -> ToolResult:
    """Format a failed job invocation response."""
    structured_content = {
        "message": "Failed to trigger remote execution job.",
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
