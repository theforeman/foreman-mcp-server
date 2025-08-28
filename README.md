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
# Standard container - mount to /app/ca.pem
podman run -it -p 8080:8080 \
  -v /path/to/your-ca-bundle.pem:/app/ca.pem:ro \
  foreman-mcp-server \
  --foreman-url https://my-foreman-instance.something.somewhere \
  --transport streamable-http

# UBI9 image - mount to /opt/app-root/src/ca.pem  
podman run -it -p 8080:8080 \
  -v /path/to/your-ca-bundle.pem:/opt/app-root/src/ca.pem:ro \
  foreman-mcp-server \
  --foreman-url https://my-foreman-instance.something.somewhere \
  --transport streamable-http
```

**Option 2: Mount to custom location**
```shell
podman run -it -p 8080:8080 \
  -v /path/to/your-ca-bundle.pem:/custom/ca.pem:ro \
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
