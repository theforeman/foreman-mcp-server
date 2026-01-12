from pydantic import Field


def register_errata_prompts(mcp, _foreman_api, _get_context):
    @mcp.prompt(
        name="Apply Errata to Hosts",
        description="A prompt for applying a specific errata to applicable hosts in Foreman using remote execution.",
    )
    async def apply_errata_prompt(
        errata_id: str = Field(description="The errata identifier (e.g., RHSA-2025:1234)"),
    ) -> str:
        prompt = f"""Help me apply the errata '{errata_id}' to hosts on my Foreman instance.

Follow these steps:

1. **Find applicable hosts**: Use the call_foreman_api_get tool to search for hosts where this errata can be installed:
   - Resource: "hosts"
   - Action: "index"
   - Params: {{"search": "installable_errata = {errata_id}"}}

   If no hosts are found, inform me and stop.

2. **Present hosts and ask for confirmation**:
   - List all the hosts found (show hostname and any relevant details like OS, environment, or host group)
   - Ask me if I want to:
     a) Apply the errata to ALL listed hosts
     b) Apply to a SUBSET of hosts (ask me to specify which ones or provide a search query)
     c) Cancel the operation

   **IMPORTANT**: Do NOT proceed to trigger the job until I explicitly confirm which hosts to target.

3. **Find the appropriate job template**: Once I confirm the target hosts, use call_foreman_api_get to list available job templates:
   - Resource: "job_templates"
   - Action: "index"
   - Params: {{"search": "name ~ errata"}}

   Look for a template that applies or installs errata (common names include "Install Errata - Katello Script Default" or similar).

4. **Trigger the remote execution job**: Use the trigger_remote_execution_job tool with:
   - job_template_id: The ID of the errata installation template
   - search_query: Use the search query based on my selection:
     - If ALL hosts: "installable_errata = {errata_id}"
     - If SUBSET: combine with my specified criteria (e.g., "installable_errata = {errata_id} AND name ~ myhost")
   - inputs: {{"errata": "{errata_id}"}} (adjust based on template requirements)
   - description: "Apply errata {errata_id}"

5. **Wait for completion**: Use the poll_task tool with the task_id returned from the job invocation. Use a reasonable timeout based on the number of hosts.

6. **Check results**: After the task completes, use call_foreman_api_get to get job details:
   - Resource: "job_invocations"
   - Action: "show"
   - Params: {{"id": <job_invocation_id>}}

7. **Report summary**: Provide me with:
   - Number of hosts targeted
   - Number of successful/failed hosts
   - Overall job status

8. **Investigate failures** (if any): If hosts failed, use call_foreman_api_get to get host-specific output:
   - Resource: "job_invocations"
   - Action: "outputs"
   - Params: {{"id": <job_invocation_id>, "host_status": "failed"}}

   Summarize what went wrong and suggest remediation steps.
"""
        return prompt
