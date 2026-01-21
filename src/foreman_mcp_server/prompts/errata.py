"""AI prompts for errata management workflows.

These prompts guide the AI through complex errata operations with
appropriate safeguards for enterprise environments.
"""


def register_errata_prompts(mcp, _foreman_api, _get_context):
    """Register errata management prompts with the MCP server."""

    @mcp.prompt(
        name="Apply Security Errata Safely",
        description=(
            "Guided workflow for safely applying security errata across environments. "
            "Includes impact analysis, staged rollout, and failure investigation."
        ),
    )
    async def apply_security_errata_safely() -> str:
        return """You are assisting with applying security errata to a Foreman/Katello managed infrastructure.

CRITICAL: Before proceeding, you MUST ask the user to identify their production lifecycle environments.

## Step 1: Clarify Production Environments

Ask the user:
"Which lifecycle environments do you consider production? Please provide the exact names as they appear in Foreman (e.g., 'Production', 'Prod', 'Live'). This is essential for safe errata application."

## Step 2: Analyze Impact

Once you have the production environments list, use `analyze_errata_impact` with:
- The errata ID the user wants to apply
- The `production_environments` parameter set to the list the user provided

Review the impact summary and present:
- Total affected hosts
- Breakdown by lifecycle environment
- Which environments are production vs non-production

## Step 3: Recommend Staged Rollout

Suggest applying errata in this order:
1. Development/Test environments first
2. Staging/QA environments second
3. Production environments last (with explicit user confirmation)

## Step 4: Apply Errata

For each environment in the rollout order:
1. Use `apply_errata` with `dry_run=True` first to show what would happen
2. After user confirms, use `apply_errata` with `dry_run=False`
3. Use `poll_task` to monitor the job
4. If failures occur, use `investigate_errata_failures` to analyze

## Step 5: Handle Failures

If any failures occur:
1. Do NOT proceed to the next environment until failures are resolved
2. Present the failure analysis and recommendations
3. Ask user how they want to proceed

## Important Safeguards

- NEVER apply errata to production without explicit user confirmation
- ALWAYS show dry_run results before actual application
- ALWAYS wait for one environment to complete before moving to the next
- If the user has not provided production environments, ask for them before proceeding
"""

    @mcp.prompt(
        name="Investigate Errata Compliance",
        description=(
            "Analyze errata compliance status across the infrastructure. "
            "Identify hosts with pending security updates."
        ),
    )
    async def investigate_errata_compliance() -> str:
        return """You are assisting with investigating errata compliance across a Foreman/Katello managed infrastructure.

## Step 1: Understand the Scope

Ask the user what they want to investigate:
- A specific erratum (e.g., RHSA-2024:1234)?
- All security errata?
- Errata for a specific hostgroup or lifecycle environment?

## Step 2: Clarify Production Classification

Ask the user:
"Which lifecycle environments do you consider production? Please provide the exact names. This helps prioritize which hosts need attention first."

## Step 3: Gather Data

Based on the scope:
- For a specific erratum: Use `analyze_errata_impact` with the errata_id and production_environments
- For general compliance: Use the Foreman API to query hosts with applicable errata

## Step 4: Present Findings

Organize the results by:
1. Production hosts with pending security errata (highest priority)
2. Non-production hosts with pending errata
3. Summary statistics

## Step 5: Recommend Actions

Based on findings, suggest:
- Which errata to prioritize
- Recommended rollout order
- Any hosts that may need special attention

Remember: Always classify environments based on user input, never assume which environments are production.
"""

    @mcp.prompt(
        name="Troubleshoot Failed Errata Application",
        description=(
            "Diagnose and resolve failures from errata application jobs."
        ),
    )
    async def troubleshoot_errata_failures() -> str:
        return """You are assisting with troubleshooting failed errata application.

## Step 1: Identify the Failed Job

Ask the user for the job invocation ID. This can be found in:
- The Foreman web UI under Monitor > Jobs
- The output from a previous `apply_errata` call
- The task details from `poll_task`

## Step 2: Analyze Failures

Use `investigate_errata_failures` with the job_invocation_id to:
- Get details on failed hosts
- Identify common error patterns
- Gather host context (OS, hostgroup, lifecycle environment)

## Step 3: Present Findings

Organize the analysis:
1. Summary: Total failures, common patterns
2. Detailed breakdown by error type
3. List of affected hosts with their specific errors

## Step 4: Provide Recommendations

Based on the error patterns, suggest:
- Immediate remediation steps
- Hosts that need manual intervention
- Whether a retry is likely to succeed

## Step 5: Plan Next Steps

Help the user decide:
- Which hosts to retry
- Whether to skip certain hosts
- If the issue requires infrastructure changes

Common issues to check for:
- Repository access problems
- Disk space issues
- Network connectivity
- Permission/sudo problems
- Package conflicts
"""
