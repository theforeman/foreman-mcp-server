from pydantic import Field


def register_errata_prompts(mcp):
    @mcp.prompt(
        name="Apply Errata to Hosts",
        description="A prompt for applying a specific errata to applicable hosts in Foreman using remote execution.",
    )
    async def apply_errata_prompt(
        errata_id: str = Field(
            description="The errata identifier (e.g., RHSA-2025:1234)"
        ),
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

3. **Find the appropriate remote execution feature**: Once I confirm the target hosts, read the allowed remote execution features resource:
   - URI: "foreman://remote_execution/allowed_features"

   Look for a feature related to errata installation (e.g., "katello_errata_install"). This resource provides the allowed features along with their job template information.

4. **Get template inputs**: Use call_foreman_api_get to read the feature's associated job template to see what inputs it accepts:
   - Resource: "job_templates"
   - Action: "show"
   - Params: {{"id": <job_template_id from the feature>}}

5. **Trigger the remote execution job**: Use the trigger_remote_execution_job tool with:
   - feature: The remote execution feature label (e.g., "katello_errata_install")
   - search_query: Use the search query based on my selection:
     - If ALL hosts: "installable_errata = {errata_id}"
     - If SUBSET: combine with my specified criteria (e.g., "installable_errata = {errata_id} AND name ~ myhost")
   - inputs: {{"errata": "{errata_id}"}} (adjust based on template requirements)
   - description: "Apply errata {errata_id}"

6. **Wait for completion**: Use the poll_task tool with the task_id returned from the job invocation. Use a reasonable timeout based on the number of hosts.

7. **Check results**: After the task completes, use call_foreman_api_get to get job details:
   - Resource: "job_invocations"
   - Action: "show"
   - Params: {{"id": <job_invocation_id>}}

8. **Report summary**: Provide me with:
   - Number of hosts targeted
   - Number of successful/failed hosts
   - Overall job status

9. **Investigate failures** (if any): If hosts failed, use call_foreman_api_get to get host-specific output:
   - Resource: "job_invocations"
   - Action: "outputs"
   - Params: {{"id": <job_invocation_id>, "host_status": "failed"}}

   Summarize what went wrong and suggest remediation steps.
"""
        return prompt

    @mcp.prompt(
        name="Add Errata to Content Views",
        description="A prompt for adding a specific errata to content views and making it available to hosts through publishing and promotion.",
    )
    async def add_errata_to_content_views_prompt(
        errata_id: str = Field(
            description="The errata identifier (e.g., RHSA-2025:1234)"
        ),
    ) -> str:
        prompt = f"""Help me add the errata '{errata_id}' to content views and make it available to hosts on my Foreman instance.

Follow these steps:

1. **Find applicable hosts**: Use the call_foreman_api_get tool to search for hosts where this errata is applicable:
   - Resource: "hosts"
   - Action: "index"
   - Params: {{"search": "applicable_errata = {errata_id}", "per_page": "all"}}

   If no hosts are found, inform me and stop.

2. **Identify content views**: From the host results, collect the unique content views attached to those hosts.
   For each host, look at the `content_facet_attributes` field which contains:
   - `content_view_id` and `content_view` (name)
   - `lifecycle_environment_id` and `lifecycle_environment` (name)
   - `content_view_version_id` (not directly in the response, we need to look it up)

   Use call_foreman_api_get to get the content view details:
   - Resource: "content_views"
   - Action: "show"
   - Params: {{"id": <content_view_id>}}

   This will show the content view versions and which environments they are in.

3. **Present findings and ask for confirmation**:
   - List the affected hosts grouped by content view and lifecycle environment
   - Show which content views need to be updated
   - Ask me if I want to:
     a) Update ALL listed content views
     b) Update only SPECIFIC content views (ask me which ones)
     c) Cancel the operation

   **IMPORTANT**: Do NOT proceed until I explicitly confirm which content views to update.

4. **Get errata database IDs**: Look up the errata to get its internal IDs:
   - Resource: "errata"
   - Action: "index"
   - Params: {{"search": "errata_id = {errata_id}"}}

   Collect the errata_id values from the results.

5. **Perform incremental content view update**: For each confirmed content view, use the incremental_content_view_update tool:
   - content_view_version_environments: List of dicts with content_view_version_id and environment_ids for each CV version
   - errata_ids: The errata IDs from step 4
   - description: "Adding errata {errata_id}"
   - resolve_dependencies: true

   Use poll_task to wait for each update to complete.

6. **Report incremental update results**: After all updates complete, summarize:
   - Which content views were updated
   - Whether each update succeeded or failed
   - The new content view version numbers created

7. **Ask about publishing**: Ask me if I want to publish new versions of the updated content views.
   If yes, for each content view:
   - Use the publish_content_view tool with the content view ID
   - Use poll_task to wait for publishing to complete
   - Report the new version created

   **IMPORTANT**: Do NOT publish without my confirmation.

8. **Ask about promotion**: After publishing, identify the lifecycle environments available for each content view:
   - Use call_foreman_api_get to list lifecycle environments:
     Resource: "lifecycle_environments"
     Action: "index"

   For each environment (e.g., Dev, Test, Production):
   - Ask me individually: "Promote to <environment_name>?"
   - Only promote to environments I confirm
   - Use the promote_content_view_version tool for confirmed environments
   - Use poll_task to wait for each promotion to complete

   **IMPORTANT**: Ask for confirmation for EACH environment individually. Do NOT batch promote without asking.

9. **Final summary**: Provide a complete summary:
   - Errata: {errata_id}
   - Content views updated (with new version numbers)
   - Environments promoted to
   - Hosts that now have access to the errata
   - Any failures or issues encountered
"""
        return prompt
