import json
from collections.abc import Sequence
from typing import Annotated

from fastmcp import Context, FastMCP
from fastmcp.tools.tool import ToolResult
from pydantic import Field
from requests.exceptions import HTTPError

from ..utils.content_utils import build_tool_result
from ..utils.utils import get_foreman_api, mcp_info_headers


def register_content_view_tools(
    mcp: FastMCP, allowed_cv_actions: Sequence[str] = ()
) -> None:
    @mcp.local_provider.tool(
        enabled="incremental_update" in allowed_cv_actions,
        description="""Performs an incremental update on one or more content view versions, adding specified errata.
This creates new minor content view versions containing the added errata and optionally promotes them to specified lifecycle environments.

Before using this tool:
1. Use call_foreman_api_get to search for hosts with applicable errata (resource: "hosts", action: "index", params: {"search": "applicable_errata = <errata_id>"})
2. Identify the content view versions attached to those hosts
3. Get the errata database IDs using call_foreman_api_get (resource: "errata", action: "index", params: {"search": "errata_id = <errata_id>"})

Returns a task ID for polling with poll_task.""",
        tags=("foreman", "katello", "api", "post", "content-view", "errata"),
        annotations={
            "title": "Incremental Content View Update",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def incremental_content_view_update(
        content_view_version_environments: Annotated[
            list[dict],
            Field(
                description=(
                    "List of dicts, each containing:\n"
                    "- content_view_version_id (int): The CV version ID\n"
                    "- environment_ids (list[int]): Lifecycle environment IDs to promote the new version to"
                )
            ),
        ],
        errata_ids: Annotated[
            list[str],
            Field(description="List of errata IDs to add (e.g., ['RHSA-2025:1234'])"),
        ],
        ctx: Context,
        description: Annotated[
            str | None,
            Field(description="Optional description for the new CV versions"),
        ] = None,
        resolve_dependencies: Annotated[
            bool,
            Field(
                description="Whether to resolve and copy dependencies (default: True)"
            ),
        ] = True,
        propagate_all_composites: Annotated[
            bool,
            Field(
                description="Whether to propagate to all composite CVs (default: False)"
            ),
        ] = False,
        update_hosts: Annotated[
            dict | None,
            Field(
                description="Optional dict for applying errata to hosts after update, containing:\n- included: {'search': '<host_search_query>'} or {'ids': [<host_ids>]}\n- excluded: {'ids': [<host_ids>]} (optional)"
            ),
        ] = None,
    ) -> ToolResult:
        """
        Perform an incremental update on content view versions to add errata.
        """
        try:
            api = get_foreman_api(ctx)

            params = {
                "content_view_version_environments": content_view_version_environments,
                "add_content": {
                    "errata_ids": errata_ids,
                },
                "resolve_dependencies": resolve_dependencies,
                "propagate_all_composites": propagate_all_composites,
            }

            if description:
                params["description"] = description

            if update_hosts:
                params["update_hosts"] = update_hosts

            response = api.call(
                "content_view_versions",
                "incremental_update",
                params,
                mcp_info_headers(ctx),
            )

            return format_incremental_update_success(response)
        except Exception as e:
            return format_content_view_failure("incremental update", e)

    @mcp.local_provider.tool(
        enabled="publish" in allowed_cv_actions,
        description="""Publishes a new version of a content view.
This creates a new content view version with the latest content from its repositories.
Returns a task ID for polling with poll_task.

Before using this tool:
1. Identify the content view ID using call_foreman_api_get (resource: "content_views", action: "index")
2. After publishing, use promote_content_view_version to make it available in lifecycle environments.""",
        tags=("foreman", "katello", "api", "post", "content-view", "publish"),
        annotations={
            "title": "Publish Content View",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def publish_content_view(
        content_view_id: Annotated[
            int, Field(description="The ID of the content view to publish")
        ],
        ctx: Context,
        description: Annotated[
            str | None, Field(description="Optional description for the new version")
        ] = None,
        environment_ids: Annotated[
            list[int] | None,
            Field(
                description="Optional list of lifecycle environment IDs to promote to after publishing"
            ),
        ] = None,
        is_force_promote: Annotated[
            bool,
            Field(
                description="Force promotion bypassing lifecycle environment restrictions (default: False)"
            ),
        ] = False,
    ) -> ToolResult:
        """
        Publish a new version of a content view.
        """
        try:
            api = get_foreman_api(ctx)

            params = {"id": content_view_id}

            if description:
                params["description"] = description

            if environment_ids:
                params["environment_ids"] = environment_ids

            if is_force_promote:
                params["is_force_promote"] = is_force_promote

            response = api.call(
                "content_views",
                "publish",
                params,
                mcp_info_headers(ctx),
            )

            return format_publish_success(response, content_view_id)
        except Exception as e:
            return format_content_view_failure("publish", e)

    @mcp.local_provider.tool(
        enabled="promote" in allowed_cv_actions,
        description="""Promotes a content view version to one or more lifecycle environments.
This makes the content view version available in the specified environments so hosts can access its content.
Returns a task ID for polling with poll_task.

Before using this tool:
1. Identify the content view version ID to promote
2. Identify the target lifecycle environment IDs using call_foreman_api_get (resource: "lifecycle_environments", action: "index")
3. Confirm with the user which environments to promote to (e.g., Dev, Test, Production)""",
        tags=("foreman", "katello", "api", "post", "content-view", "promote"),
        annotations={
            "title": "Promote Content View Version",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def promote_content_view_version(
        content_view_version_id: Annotated[
            int, Field(description="The ID of the content view version to promote")
        ],
        environment_ids: Annotated[
            list[int],
            Field(description="List of lifecycle environment IDs to promote to"),
        ],
        ctx: Context,
        description: Annotated[
            str | None, Field(description="Optional description for the promotion")
        ] = None,
        force: Annotated[
            bool,
            Field(
                description="Force promotion bypassing lifecycle environment restrictions (default: False)"
            ),
        ] = False,
    ) -> ToolResult:
        """
        Promote a content view version to lifecycle environments.
        """
        try:
            api = get_foreman_api(ctx)

            params = {
                "id": content_view_version_id,
                "environment_ids": environment_ids,
            }

            if description:
                params["description"] = description

            if force:
                params["force"] = force

            response = api.call(
                "content_view_versions",
                "promote",
                params,
                mcp_info_headers(ctx),
            )

            return format_promote_success(
                response, content_view_version_id, environment_ids
            )
        except Exception as e:
            return format_content_view_failure("promote", e)


def format_incremental_update_success(response: dict) -> ToolResult:
    """Format a successful incremental update response."""
    # The response may contain task info or a list of updated versions
    task_id = None
    if isinstance(response, dict):
        task = response.get("task")
        if isinstance(task, dict):
            task_id = task.get("id")
        elif response.get("id"):
            # Direct task response
            task_id = response.get("id")

    structured_content = {
        "message": "Incremental content view update triggered successfully.",
        "task_id": task_id,
        "response": response,
    }
    return build_tool_result(structured_content)


def format_publish_success(response: dict, content_view_id: int) -> ToolResult:
    """Format a successful publish response."""
    task_id = None
    if isinstance(response, dict):
        task_id = response.get("id")

    structured_content = {
        "message": f"Content view {content_view_id} publish triggered successfully.",
        "task_id": task_id,
        "content_view_id": content_view_id,
        "response": response,
    }
    return build_tool_result(structured_content)


def format_promote_success(
    response: dict, version_id: int, environment_ids: list[int]
) -> ToolResult:
    """Format a successful promote response."""
    task_id = None
    if isinstance(response, dict):
        task_id = response.get("id")

    structured_content = {
        "message": f"Content view version {version_id} promotion triggered successfully.",
        "task_id": task_id,
        "content_view_version_id": version_id,
        "environment_ids": environment_ids,
        "response": response,
    }
    return build_tool_result(structured_content)


def format_content_view_failure(operation: str, exception: Exception) -> ToolResult:
    """Format a failed content view operation response."""
    structured_content = {
        "message": f"Failed to {operation} content view.",
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
