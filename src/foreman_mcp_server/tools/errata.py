"""AI-oriented errata management tools.

These tools encapsulate complex multi-step workflows for errata management,
reducing token usage and providing enterprise-appropriate guardrails.
"""

from typing import Optional

from fastmcp.tools.tool import ToolResult

from ..utils.content_utils import build_tool_result
from ..utils.utils import get_foreman_api, mcp_info_headers


def register_errata_tools(mcp, foreman_api, get_context):
    """Register errata management tools with the MCP server."""

    @mcp.tool(
        description=(
            "Analyze the impact of an erratum across lifecycle environments. "
            "Returns affected hosts grouped by lifecycle environment with counts. "
            "If production_environments list is provided, hosts in those environments "
            "are flagged as production. If not provided, returns raw environment data "
            "and you should ask the user which environments they consider production."
        ),
        tags=("foreman", "katello", "errata", "analysis", "remote"),
        annotations={
            "title": "Analyze Errata Impact",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def analyze_errata_impact(
        errata_id: str,
        production_environments: Optional[list[str]] = None,
    ) -> ToolResult:
        """Analyze errata impact across lifecycle environments.

        Args:
            errata_id: The errata ID (e.g., 'RHSA-2024:1234')
            production_environments: Optional list of lifecycle environment names
                that are considered production. If not provided, returns raw data
                for all environments.

        Returns:
            Impact analysis with affected hosts grouped by environment.
        """
        try:
            api = foreman_api or get_foreman_api(get_context)
            headers = mcp_info_headers(get_context)

            # Fetch the erratum details
            erratum_response = api.call(
                "errata",
                "index",
                {"search": f"errata_id={errata_id}", "per_page": 1},
                headers,
            )
            errata_results = erratum_response.get("results", [])
            if not errata_results:
                return build_tool_result({
                    "success": False,
                    "error": f"Erratum '{errata_id}' not found",
                })

            erratum = errata_results[0]

            # Fetch all hosts affected by this erratum
            hosts_response = api.call(
                "hosts",
                "index",
                {
                    "search": f"applicable_errata = {errata_id}",
                    "per_page": 1000,
                },
                headers,
            )
            affected_hosts = hosts_response.get("results", [])

            # Group hosts by lifecycle environment
            environments = {}
            hosts_without_environment = []

            for host in affected_hosts:
                content_facet = host.get("content_facet_attributes", {})
                lce = content_facet.get("lifecycle_environment", {})
                lce_name = lce.get("name") if lce else None

                if lce_name:
                    if lce_name not in environments:
                        environments[lce_name] = {
                            "name": lce_name,
                            "hosts": [],
                            "count": 0,
                        }
                    environments[lce_name]["hosts"].append({
                        "name": host.get("name"),
                        "id": host.get("id"),
                    })
                    environments[lce_name]["count"] += 1
                else:
                    hosts_without_environment.append({
                        "name": host.get("name"),
                        "id": host.get("id"),
                    })

            # Add production flag if production_environments is provided
            if production_environments:
                for env_name, env_data in environments.items():
                    env_data["is_production"] = env_name in production_environments

                production_hosts = sum(
                    env["count"]
                    for env in environments.values()
                    if env.get("is_production", False)
                )
                non_production_hosts = sum(
                    env["count"]
                    for env in environments.values()
                    if not env.get("is_production", False)
                )

                result = {
                    "success": True,
                    "erratum": {
                        "id": erratum.get("id"),
                        "errata_id": errata_id,
                        "title": erratum.get("title"),
                        "type": erratum.get("type"),
                        "severity": erratum.get("severity"),
                        "issued": erratum.get("issued"),
                    },
                    "impact_summary": {
                        "total_affected_hosts": len(affected_hosts),
                        "production_hosts": production_hosts,
                        "non_production_hosts": non_production_hosts,
                        "hosts_without_environment": len(hosts_without_environment),
                        "environments_affected": len(environments),
                    },
                    "environments": environments,
                    "hosts_without_environment": hosts_without_environment,
                    "production_environments_config": production_environments,
                }
            else:
                # Return raw data and prompt for clarification
                result = {
                    "success": True,
                    "erratum": {
                        "id": erratum.get("id"),
                        "errata_id": errata_id,
                        "title": erratum.get("title"),
                        "type": erratum.get("type"),
                        "severity": erratum.get("severity"),
                        "issued": erratum.get("issued"),
                    },
                    "impact_summary": {
                        "total_affected_hosts": len(affected_hosts),
                        "environments_affected": len(environments),
                        "hosts_without_environment": len(hosts_without_environment),
                    },
                    "environments": environments,
                    "hosts_without_environment": hosts_without_environment,
                    "requires_clarification": True,
                    "clarification_needed": (
                        "To identify which hosts are in production environments, "
                        "please specify the 'production_environments' parameter with "
                        "a list of lifecycle environment names you consider production. "
                        f"Available environments: {list(environments.keys())}"
                    ),
                }

            return build_tool_result(result)

        except Exception as e:
            return build_tool_result({
                "success": False,
                "error": str(e),
            })

    @mcp.tool(
        description=(
            "Apply an erratum to a specific lifecycle environment using remote execution. "
            "Returns a task ID for tracking. This is a destructive operation that "
            "modifies systems. Use analyze_errata_impact first to understand scope."
        ),
        tags=("foreman", "katello", "errata", "rex", "remote", "destructive"),
        annotations={
            "title": "Apply Errata",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def apply_errata(
        errata_id: str,
        lifecycle_environment: str,
        hostgroup: Optional[str] = None,
        host_ids: Optional[list[int]] = None,
        dry_run: bool = False,
    ) -> ToolResult:
        """Apply an erratum to hosts in a lifecycle environment.

        Args:
            errata_id: The errata ID to apply (e.g., 'RHSA-2024:1234')
            lifecycle_environment: Target lifecycle environment name
            hostgroup: Optional hostgroup name to further filter targets
            host_ids: Optional list of specific host IDs to target
            dry_run: If True, only show what would be done without executing

        Returns:
            Task information for tracking the job execution.
        """
        try:
            api = foreman_api or get_foreman_api(get_context)
            headers = mcp_info_headers(get_context)

            # Build the search query
            search_parts = [
                f"applicable_errata = {errata_id}",
                f"lifecycle_environment = {lifecycle_environment}",
            ]
            if hostgroup:
                search_parts.append(f"hostgroup = {hostgroup}")

            search_query = " AND ".join(search_parts)

            # Find affected hosts
            hosts_response = api.call(
                "hosts",
                "index",
                {"search": search_query, "per_page": 1000},
                headers,
            )
            affected_hosts = hosts_response.get("results", [])

            # Filter by specific host_ids if provided
            if host_ids:
                affected_hosts = [h for h in affected_hosts if h.get("id") in host_ids]

            if not affected_hosts:
                return build_tool_result({
                    "success": False,
                    "error": (
                        f"No hosts found matching criteria: "
                        f"errata={errata_id}, environment={lifecycle_environment}"
                        + (f", hostgroup={hostgroup}" if hostgroup else "")
                    ),
                })

            target_host_ids = [h.get("id") for h in affected_hosts]

            if dry_run:
                return build_tool_result({
                    "success": True,
                    "dry_run": True,
                    "message": "Dry run - no changes made",
                    "would_apply_to": {
                        "errata_id": errata_id,
                        "lifecycle_environment": lifecycle_environment,
                        "hostgroup": hostgroup,
                        "host_count": len(target_host_ids),
                        "hosts": [
                            {"id": h.get("id"), "name": h.get("name")}
                            for h in affected_hosts
                        ],
                    },
                })

            # Find the errata install job template
            templates_response = api.call(
                "job_templates",
                "index",
                {"search": "name ~ \"Install Errata\"", "per_page": 10},
                headers,
            )
            templates = templates_response.get("results", [])

            if not templates:
                return build_tool_result({
                    "success": False,
                    "error": "Could not find 'Install Errata' job template",
                })

            template = templates[0]

            # Invoke the remote execution job
            job_invocation_params = {
                "job_invocation": {
                    "job_template_id": template.get("id"),
                    "targeting_type": "static_query",
                    "search_query": search_query,
                    "inputs": {
                        "errata": errata_id,
                    },
                }
            }

            job_response = api.call(
                "job_invocations",
                "create",
                job_invocation_params,
                headers,
            )

            return build_tool_result({
                "success": True,
                "message": f"Errata installation job started for {len(target_host_ids)} hosts",
                "job_invocation": {
                    "id": job_response.get("id"),
                    "description": job_response.get("description"),
                    "status": job_response.get("status"),
                    "task_id": job_response.get("dynflow_task", {}).get("id"),
                },
                "targets": {
                    "errata_id": errata_id,
                    "lifecycle_environment": lifecycle_environment,
                    "host_count": len(target_host_ids),
                },
                "next_steps": (
                    "Use poll_task with the task_id to monitor progress, or "
                    "use investigate_errata_failures if the job fails."
                ),
            })

        except Exception as e:
            return build_tool_result({
                "success": False,
                "error": str(e),
            })

    @mcp.tool(
        description=(
            "Investigate failures from an errata application job. "
            "Fetches job output and host details for failed hosts."
        ),
        tags=("foreman", "katello", "errata", "rex", "troubleshooting", "remote"),
        annotations={
            "title": "Investigate Errata Failures",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def investigate_errata_failures(
        job_invocation_id: int,
        max_failures: int = 10,
    ) -> ToolResult:
        """Investigate failures from an errata application job.

        Args:
            job_invocation_id: The job invocation ID to investigate
            max_failures: Maximum number of failures to analyze (default 10)

        Returns:
            Detailed failure analysis with host information and error messages.
        """
        try:
            api = foreman_api or get_foreman_api(get_context)
            headers = mcp_info_headers(get_context)

            # Get job invocation details
            job_response = api.call(
                "job_invocations",
                "show",
                {"id": job_invocation_id},
                headers,
            )

            # Get failed hosts
            failed_hosts_response = api.call(
                "job_invocations",
                "hosts",
                {"id": job_invocation_id, "search": "status = failed"},
                headers,
            )
            failed_hosts = failed_hosts_response.get("results", [])[:max_failures]

            failures = []
            for host_entry in failed_hosts:
                host_id = host_entry.get("host_id")
                host_name = host_entry.get("host_name")

                # Get job output for this host
                try:
                    output_response = api.call(
                        "job_invocations",
                        "output",
                        {"id": job_invocation_id, "host_id": host_id},
                        headers,
                    )
                    output = output_response.get("output", [])
                    error_output = "\n".join(
                        line.get("output", "")
                        for line in output
                        if line.get("output_type") in ("stderr", "debug")
                    )
                except Exception as e:
                    error_output = f"Could not fetch output: {e}"

                # Get host details for context
                try:
                    host_response = api.call(
                        "hosts",
                        "show",
                        {"id": host_id},
                        headers,
                    )
                    host_details = {
                        "os": host_response.get("operatingsystem_name"),
                        "hostgroup": host_response.get("hostgroup_name"),
                        "content_view": host_response.get(
                            "content_facet_attributes", {}
                        ).get("content_view", {}).get("name"),
                        "lifecycle_environment": host_response.get(
                            "content_facet_attributes", {}
                        ).get("lifecycle_environment", {}).get("name"),
                    }
                except Exception:
                    host_details = {}

                failures.append({
                    "host_id": host_id,
                    "host_name": host_name,
                    "error_output": error_output[:2000],  # Truncate long outputs
                    "host_details": host_details,
                })

            # Analyze common patterns
            error_patterns = {}
            for failure in failures:
                error = failure.get("error_output", "")[:200]
                if error:
                    error_patterns[error] = error_patterns.get(error, 0) + 1

            total_failed = failed_hosts_response.get("total", 0)

            return build_tool_result({
                "success": True,
                "job_invocation": {
                    "id": job_invocation_id,
                    "description": job_response.get("description"),
                    "status": job_response.get("status"),
                    "succeeded": job_response.get("succeeded"),
                    "failed": job_response.get("failed"),
                    "pending": job_response.get("pending"),
                },
                "failure_summary": {
                    "total_failed": total_failed,
                    "analyzed": len(failures),
                    "common_patterns": [
                        {"pattern": p, "count": c}
                        for p, c in sorted(
                            error_patterns.items(), key=lambda x: x[1], reverse=True
                        )[:5]
                    ],
                },
                "failures": failures,
                "recommendations": _generate_failure_recommendations(failures),
            })

        except Exception as e:
            return build_tool_result({
                "success": False,
                "error": str(e),
            })


def _generate_failure_recommendations(failures: list) -> list[str]:
    """Generate recommendations based on failure patterns."""
    recommendations = []

    for failure in failures:
        error = failure.get("error_output", "").lower()

        if "no package" in error or "nothing to do" in error:
            if "Package already installed" not in recommendations:
                recommendations.append(
                    "Some hosts may already have the update or the package "
                    "is not applicable. Check content view and lifecycle environment."
                )

        if "connection" in error or "timeout" in error or "unreachable" in error:
            if "Connectivity issues" not in recommendations:
                recommendations.append(
                    "Connectivity issues detected. Check network access and "
                    "ensure the remote execution proxy can reach affected hosts."
                )

        if "permission" in error or "denied" in error or "sudo" in error:
            if "Permission issues" not in recommendations:
                recommendations.append(
                    "Permission issues detected. Verify the remote execution user "
                    "has appropriate sudo privileges on the target hosts."
                )

        if "yum" in error or "dnf" in error or "rpm" in error:
            if "Package manager" not in recommendations:
                recommendations.append(
                    "Package manager errors detected. Check for repository access, "
                    "disk space, or transaction lock issues on affected hosts."
                )

    if not recommendations:
        recommendations.append(
            "Review the error outputs above for specific failure causes. "
            "Consider checking host connectivity, repository access, and disk space."
        )

    return recommendations
