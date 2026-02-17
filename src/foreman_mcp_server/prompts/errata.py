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

1. **Validate the errata exists**: Verify the errata is known to Foreman:
   - Resource: "errata"
   - Action: "index"
   - Params: {{"search": "errata_id = {errata_id}"}}

   If no results are found, inform me and stop — the errata may not be synced yet.
   The human-readable errata ID (e.g., '{errata_id}') is passed directly to the
   incremental update tool — no conversion to database IDs is needed.

2. **Find applicable hosts**: Use the call_foreman_api_get tool to search for hosts where this errata is applicable:
   - Resource: "hosts"
   - Action: "index"
   - Params: {{"search": "applicable_errata = {errata_id}", "per_page": 100}}

   If the results indicate more pages are available (check `total` vs returned count),
   fetch additional pages to get the full list of affected hosts.

   If no hosts are found, inform me and stop.

3. **Identify content views and versions**: From the host results, collect the unique content views attached to those hosts.
   For each host, extract from `content_facet_attributes`:
   - `content_view_id` and `content_view` (name)
   - `lifecycle_environment_id` and `lifecycle_environment` (name)

   Then, for each unique `content_view_id`, call:
   - Resource: "content_views"
   - Action: "show"
   - Params: {{"id": <content_view_id>}}

   From the response, look at the `versions` array. Each version has an `environment_ids` list.
   Match the version whose `environment_ids` includes the host's `lifecycle_environment_id` —
   that gives you the `content_view_version_id` to use for the incremental update.

   Note: the incremental update API can only target environments where the CV version
   is already promoted. Collect the full list of environments per CV version for use in step 4.

4. **Present findings and ask for confirmation**:
   - List the affected hosts grouped by content view and lifecycle environment
   - Show which content views need to be updated
   - Ask me if I want to:
     a) Update ALL listed content views
     b) Update only SPECIFIC content views (ask me which ones)
     c) Cancel the operation

   **IMPORTANT**: Do NOT proceed until I explicitly confirm which content views to update.

   Also, for each selected content view, show the environments where its version is currently promoted
   and ask which environments to include in the incremental update.
   Only environments where the CV version is already deployed are valid targets.

   Finally, ask me if I also want to apply the errata to the affected hosts after the update.
   If yes, the `update_hosts` parameter will be included in the incremental update call,
   which triggers a Remote Execution job to install the errata on hosts.

   **IMPORTANT**: Do NOT proceed until I confirm the content views, target environments,
   and whether to apply errata to hosts.

5. **Perform incremental content view update**: For each confirmed content view, use the incremental_content_view_update tool:
   - content_view_version_environments: List of dicts with content_view_version_id and
     environment_ids as confirmed by the user in step 4.
     The environment_ids MUST only include environments where the CV version is currently promoted.
   - errata_ids: ["{errata_id}"] (the human-readable errata ID, passed directly)
   - description: "Adding errata {errata_id}"
   - resolve_dependencies: true
   - propagate_all_composites: If any of the selected content views are components of composite
     content views, ask me whether to propagate the incremental update to all composite CVs
     that include the updated components. If yes, set propagate_all_composites to true.
   - update_hosts: If the user confirmed host application in step 4, include:
     {{"included": {{"search": "applicable_errata = {errata_id}"}}}}
     This triggers a Remote Execution job to install the errata on hosts.

   Use poll_task to wait for each update to complete.

   **IMPORTANT**: Do NOT perform the update without my confirmation of which content views to update and which environments to promote to.

6. **Final summary**: Provide a complete summary:
   - Errata: {errata_id}
   - Content views updated (with new version numbers)
   - Environments promoted to
   - Whether errata was applied to hosts
   - Hosts that now have access to the errata
   - Any failures or issues encountered
"""
        return prompt
