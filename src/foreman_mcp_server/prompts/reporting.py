def register_reporting_prompts(mcp, _foreman_api):
    @mcp.prompt(
        name="Basic Subnets Static Report",
        description="A prompt for generating a static report of all subnets in Foreman.",
    )
    async def basic_subnets_static_report() -> str:
        prompt = (
            "Generate a static report of all subnets on my Foreman instance."
            " Read API documentation for each of the needed resources before doing any searches."
            " For each subnet, report its name, address, network mask and number of hosts which are assigned to it."
        )
        return prompt

    @mcp.prompt(
        name="Basic Hosts Pending Security Updates Static Report",
        description="A prompt for generating a static report of hosts with pending security updates in Foreman.",
    )
    async def basic_hosts_pending_sec_updates_static_report() -> str:
        prompt = (
            "Generate a static report of all hosts on my Foreman instance which have pending security updates."
            " For each host, include its name and number of pending updates."
        )
        return prompt
