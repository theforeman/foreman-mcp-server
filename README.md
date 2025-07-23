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
  --transport streamable-http
  --no-verify-ssl
```

Default values if not provided:
```shell
  --foreman-url https://$hostname
  --foreman-username admin
  --foreman-password changeme
  --log-level INFO
  --host '127.0.0.1'
  --port 8080
  --transport streamable-http
  --verify-ssl
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
  --foreman-username $FOREMAN_USERNAME \
  --foreman-password $FOREMAN_PASSWORD \
  --log-level debug \
  --host localhost \
  --port 8080 \
  --transport streamable-http
```

## Configure VSCode

```
# settings.json
{
    "mcp": {
        "servers": {
            "foreman": {
                "url": "http://127.0.0.1:8080/mcp/sse"
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
      "args": ["--directory", "/home/$USER/foreman-mcp-server", "run","foreman-mcp-server", "--transport", "stdio"],
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
