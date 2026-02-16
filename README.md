# foreman-mcp-server

# How to run

# Using VSCode with Copilot

## Start the server via uv

```shell
uv run foreman-mcp-server \
  --foreman-url https://foreman.example.com \
  --foreman-username $FOREMAN_USERNAME \
  --foreman-password $FOREMAN_PASSWORD \
  --log-level debug \
  --host localhost \
  --port 8080 \
  --transport stdio \
  --no-verify-ssl
```

Default values if not provided:
```shell
  --foreman-url https://$hostname
  --log-level INFO
  --host '127.0.0.1'
  --port 8080
  --transport streamable-http
  --verify-ssl
```

### Using custom CA certificates

If your Foreman instance uses a custom CA certificate, you have several options:

1. Use the `--ca-bundle` option or `FOREMAN_CA_BUNDLE` environment variable:
```shell
uv run foreman-mcp-server \
  --foreman-url https://foreman.example.com \
  --foreman-username $FOREMAN_USERNAME \
  --foreman-password $FOREMAN_PASSWORD \
  --ca-bundle /path/to/ca-bundle.pem
```

2. Place your CA certificate as `./ca.pem` in the working directory (automatically detected):
```shell
cp /path/to/ca-bundle.pem ./ca.pem
uv run foreman-mcp-server \
  --foreman-url https://foreman.example.com \
  --foreman-username $FOREMAN_USERNAME \
  --foreman-password $FOREMAN_PASSWORD
```

## Start the server via podman

First, build the container:

```
podman build -t foreman-mcp-server .
```

Now run the container:

```shell
podman run -it -p 8080:8080 foreman-mcp-server \
  --foreman-url https://my-foreman-instance.something.somewhere \
  --log-level debug \
  --host localhost \
  --port 8080 \
  --transport streamable-http
```

### Using custom CA certificates with containers

To use custom CA certificates with the container, you can either mount your CA bundle to the default `ca.pem` location (automatically detected) or specify a custom path:

**Option 1: Mount to default location (recommended)**
```shell
# Standard container or UBI9 image - mount to /app/ca.pem
podman run -it -p 8080:8080 \
  -v /path/to/your-ca-bundle.pem:/app/ca.pem:ro,Z \
  foreman-mcp-server \
  --foreman-url https://my-foreman-instance.something.somewhere \
  --transport streamable-http

**Option 2: Mount to custom location**
```shell
podman run -it -p 8080:8080 \
  -v /path/to/your-ca-bundle.pem:/custom/ca.pem:ro,Z \
  foreman-mcp-server \
  --foreman-url https://my-foreman-instance.something.somewhere \
  --ca-bundle /custom/ca.pem \
  --transport streamable-http
```

## Configure VSCode

```
# settings.json
{
    "mcp": {
        "servers": {
            "foreman": {
                "url": "http://127.0.0.1:8080/mcp/sse",
                "type": "http",
                  "headers": {
                    "FOREMAN_USERNAME": "login",
                    "FOREMAN_TOKEN": "token"
                  }
            }
        }
    },
}
```

## Run VSCode client

 - Press Ctrl+Shift+P
 - Select MCP: List Servers command
 - Select foreman
 - Press Start Server

## Using in Copilot Chat

 - Press Ctrl+Alt+I to open the chat
 - In Configure Tools select the MCP tools only
 - Prompts can be listed in the chat, e.g. /mcp.foreman.basic_hosts_pending_sec_updates_static_report
 - Resources can be attached via Add Context... > MCP Resources > resource

# Using MCP Inspector

For use with mcp inspector
1) Start the inspector with `npx @modelcontextprotocol/inspector`
2) Open `http://localhost:6274` in your browser
3) Set `Type` to `Streamable HTTP` and `URL` to `http://localhost:8080/mcp`
4) Click connect

# Using Claude Desktop on Linux

Note: this is highly experimental. Tested in a virtual machine running CentOS Stream 9.

## Installation

 - Follow installation steps https://github.com/bsneed/claude-desktop-fedora?tab=readme-ov-file#1-fedora-package-new
 - If it doesn't launch, try `npm i -g electron

## Configuration

```
# ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "foreman": {
      "command": "uv",
      "args": ["--directory", "/home/$USER/foreman-mcp-server", "run","foreman-mcp-server", "--transport", "stdio", "--foreman-username", "login", "--foreman-password", "password/token"],
    }
  }
}
```

To use custom CA certificates with Claude Desktop:
```
# ~/.config/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "foreman": {
      "command": "uv",
      "args": ["--directory", "/home/$USER/foreman-mcp-server", "run","foreman-mcp-server", "--transport", "stdio", "--foreman-username", "login", "--foreman-password", "password/token", "--ca-bundle", "/path/to/ca-bundle.pem"],
    }
  }
}
```

## Run Claude client

This will launch UI application, log in into your account. It will start and connect to the MCP server automatically.

```shell
claude-desktop
```

 - Click `+` button > Add from foreman: > Select any of Prompts and Resources from the server
 - Click Configuration button to select Tools from the server

# Remote Execution Features

The MCP server can trigger remote execution jobs on Foreman hosts. This functionality is **opt-in** and disabled by default for security reasons.

## Enabling Remote Execution

To enable remote execution, you must explicitly specify which remote execution features are allowed using the `--allowed-rex-features` option or the `FOREMAN_ALLOWED_REX_FEATURES` environment variable:

```shell
uv run foreman-mcp-server \
  --foreman-url https://foreman.example.com \
  --foreman-username $FOREMAN_USERNAME \
  --foreman-password $FOREMAN_PASSWORD \
  --allowed-rex-features "katello_errata_install,katello_package_install"
```

Or using the environment variable:

```shell
export FOREMAN_ALLOWED_REX_FEATURES="katello_errata_install,katello_package_install"
uv run foreman-mcp-server ...
```

## How It Works

1. **Allowlist-based security**: Only remote execution features explicitly listed in `--allowed-rex-features` can be triggered. Any attempt to use a feature not on the list will be rejected.

2. **Available features resource**: When allowed features are configured, a resource becomes available at `foreman://remote_execution/allowed_features`. This resource returns information about each allowed feature, including:
   - Feature label, ID, name, and description
   - Associated job template ID and name
   - Any errors (e.g., if the feature doesn't exist in Foreman)

3. **Trigger tool**: The `trigger_remote_execution_job` tool is only enabled when at least one feature is allowed. To use it, the AI agent should:
   1. Read the "Allowed Remote Execution Features" resource to see available features
   2. Pick the appropriate feature for the task
   3. Use `call_foreman_api_get` to read the feature's job template (`resource: "job_templates"`, `action: "show"`) to see what inputs it accepts
   4. Call `trigger_remote_execution_job` with the feature label, search query, and appropriate inputs

## Common Remote Execution Features

Here are some commonly used remote execution feature labels:

| Feature Label | Description |
|---------------|-------------|
| `katello_errata_install` | Install errata on hosts |
| `katello_package_install` | Install packages on hosts |
| `katello_package_update` | Update packages on hosts |
| `katello_package_remove` | Remove packages from hosts |
| `katello_host_tracer_resolve` | Resolve Tracer-detected services |

To find all available features in your Foreman instance, you can use the API:
```shell
curl -u $USER:$PASSWORD https://foreman.example.com/api/remote_execution_features
```

# Content View Actions

The MCP server can publish, promote, and incrementally update content views. This functionality is **opt-in** and disabled by default for security reasons.

## Enabling Content View Actions

To enable content view actions, you must explicitly specify which actions are allowed using the `--allowed-cv-actions` option or the `FOREMAN_ALLOWED_CV_ACTIONS` environment variable:

```shell
uv run foreman-mcp-server \
  --foreman-url https://foreman.example.com \
  --foreman-username $FOREMAN_USERNAME \
  --foreman-password $FOREMAN_PASSWORD \
  --allowed-cv-actions "publish,promote,incremental_update"
```

Or using the environment variable:

```shell
export FOREMAN_ALLOWED_CV_ACTIONS="publish,promote,incremental_update"
uv run foreman-mcp-server ...
```

## How It Works

1. **Allowlist-based security**: Only content view actions explicitly listed in `--allowed-cv-actions` can be triggered. If the option is not set or empty, all content view tools are disabled.

2. **Available tools**: When specific actions are allowed, the corresponding tools become enabled:

| Action | Tool | Description |
|--------|------|-------------|
| `publish` | `publish_content_view` | Publishes a new version of a content view |
| `promote` | `promote_content_view_version` | Promotes a content view version to lifecycle environments |
| `incremental_update` | `incremental_content_view_update` | Performs an incremental update adding errata to content view versions |

3. **Usage flow**: To use the content view tools, the AI agent should:
   1. Use `call_foreman_api_get` to find the content view (resource: `"content_views"`, action: `"index"`)
   2. Publish a new version with `publish_content_view`
   3. Promote the version with `promote_content_view_version`
   4. Use `poll_task` to monitor the task progress
