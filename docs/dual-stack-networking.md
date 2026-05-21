# Dual-Stack (IPv4 + IPv6) Networking in Containers

This document explains why a containerized Python server cannot listen on both
IPv4 and IPv6 by default, and how foreman-mcp-server solves it.

## The Goal

Run a container so that the service inside is reachable on both IPv4
(`127.0.0.1`, `0.0.0.0`) and IPv6 (`::1`, `::`) without requiring two
separate port mappings or two server processes.

## Background: Dual-Stack Sockets on Linux

On Linux, an IPv6 socket can accept IPv4 connections through **IPv4-mapped
IPv6 addresses** (`::ffff:x.x.x.x`). This is controlled by the socket option
`IPV6_V6ONLY`:

- `IPV6_V6ONLY=0` — the socket accepts both IPv6 and IPv4 connections
  (dual-stack)
- `IPV6_V6ONLY=1` — the socket accepts IPv6 only

The system-wide default is set by `/proc/sys/net/ipv6/bindv6only`. On most
Linux systems this is `0` (dual-stack enabled). A program that creates an
`AF_INET6` socket and binds to `::` without explicitly setting `IPV6_V6ONLY`
inherits this default and gets dual-stack for free.

## The Problem: Three Layers That Break Dual-Stack

### Layer 1: Python's asyncio Forces IPv6-Only

Python's `asyncio.BaseEventLoop.create_server()` **always** sets
`IPV6_V6ONLY=True` on IPv6 sockets, regardless of the system default:

```python
# cpython/Lib/asyncio/base_events.py
# (inside create_server)
if af == socket.AF_INET6 and hasattr(socket, 'IPPROTO_IPV6'):
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
```

This is intentional — asyncio resolves the given host via `getaddrinfo`, which
may return both IPv4 and IPv6 results, and creates separate sockets for each.
Setting `IPV6_V6ONLY=True` prevents conflicts between the IPv6 and IPv4
sockets binding to the same port.

However, when a specific host like `::` is given (not `None` or `localhost`),
`getaddrinfo` returns only the IPv6 entry. asyncio creates one IPv6 socket,
forces it to be IPv6-only, and no IPv4 socket is created. Result: IPv6 works,
IPv4 doesn't.

### Layer 2: Uvicorn Doesn't Expose Socket Options

Uvicorn is the ASGI server that runs underneath FastMCP. It has two code paths
for socket creation:

1. **`Config.bind_socket()`** (used in multi-worker mode) — creates the socket
   directly. For IPv6, it creates an `AF_INET6` socket and sets
   `SO_REUSEADDR`, but **never touches `IPV6_V6ONLY`**. On most Linux systems
   this would inherit `IPV6_V6ONLY=0` (dual-stack). However, this path is only
   used when running multiple workers.

2. **`loop.create_server(host=..., port=...)`** (single-worker, the default) —
   delegates to asyncio, which forces `IPV6_V6ONLY=True` as described above.

Uvicorn provides no configuration option to set `IPV6_V6ONLY` or any other
socket option. The `host` parameter is typed as `str` (not a list), so there
is no way to bind to multiple addresses either.

### Layer 3: Podman/Pasta Port Forwarding is L4, Not L3

Rootless Podman uses **pasta** for networking. Unlike traditional iptables/
nftables DNAT (which netavark uses for rootful containers), pasta operates at
**Layer 4** — it creates real TCP/UDP sockets on both the host and inside the
container namespace, and relays data between them.

When you run `podman run -p 8080:8080`, Podman tells pasta to forward port
8080. Pasta creates a listening socket on `*:8080` (dual-stack) on the host
side. When an IPv4 connection arrives, pasta opens a **new IPv4 connection**
to the container. When an IPv6 connection arrives, pasta opens an IPv6
connection.

This means the server inside the container must have a listener matching the
IP family of the incoming connection. If the server only listens on `::` (IPv6)
and asyncio has forced `IPV6_V6ONLY=True`, pasta's IPv4 forwarding has nowhere
to connect and the connection fails.

For comparison, rootful Podman with netavark uses iptables/nftables DNAT rules
which operate at the packet level and can route IPv4 packets to an IPv6
destination via address mapping. Pasta cannot do this.

### The Combined Effect

```
Host (IPv4 client)
  → pasta host-side socket (*:8080, dual-stack) ✓ accepts IPv4
    → pasta creates IPv4 connection inside namespace
      → container server on [::]:8080 with IPV6_V6ONLY=1
        ✗ refuses IPv4 connection → connection reset
```

## The Solution

### What We Changed

Instead of calling `mcp.run()` (which calls uvicorn, which calls
`asyncio.create_server`), we create the socket ourselves with the correct
options and hand it to uvicorn via `Server.serve(sockets=[sock])`:

```python
sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)  # dual-stack
sock.bind(("::", port))

config = uvicorn.Config(app, ...)
server = uvicorn.Server(config)
await server.serve(sockets=[sock])  # bypasses asyncio socket creation
```

When `sockets` is passed to `Server.serve()`, uvicorn calls
`loop.create_server(sock=sock)` — when asyncio receives a pre-bound socket,
it uses it as-is without setting any socket options.

### What We Changed in the Containerfile

The default `HOST` environment variable was changed from `0.0.0.0` to `::`.
With our socket creation code, `::` now means "listen on all interfaces, both
IPv4 and IPv6" instead of "listen on IPv6 only."

### The Result

```
Host (IPv4 client)
  → pasta host-side socket (*:8080, dual-stack) ✓ accepts IPv4
    → pasta creates IPv4 connection inside namespace
      → container server on [::]:8080 with IPV6_V6ONLY=0
        ✓ accepts IPv4 via mapped address → works

Host (IPv6 client)
  → pasta host-side socket (*:8080, dual-stack) ✓ accepts IPv6
    → pasta creates IPv6 connection inside namespace
      → container server on [::]:8080
        ✓ accepts IPv6 natively → works
```

## How to Run

The simplest invocation — dual-stack by default, no flags needed:

```bash
podman run -d -p 8080:8080 foreman-mcp-server:latest \
  --foreman-url https://foreman.example.com
```

This works because:
- `-p 8080:8080` with no host IP tells pasta to bind `*:8080` (both families)
- `ENV HOST=::` in the Containerfile makes the server bind to `::` with
  `IPV6_V6ONLY=0`

## Key References

| Component | File | Relevant Code |
|-----------|------|---------------|
| asyncio IPV6_V6ONLY | `cpython/Lib/asyncio/base_events.py` | `create_server()` sets `IPV6_V6ONLY=True` |
| uvicorn socket creation | `uvicorn/config.py:538` | `bind_socket()` — no `IPV6_V6ONLY` option |
| uvicorn server startup | `uvicorn/server.py:104` | `startup(sockets=...)` — pre-bound socket path |
| pasta port forwarding | `podman/../pasta/pasta_linux.go:214` | Translates `-p` to pasta `-t` args |
| pasta L4 forwarding | `man pasta` | `-t` option, L4 socket translation |
| netavark (rootful) | `netavark/src/firewall/nft.rs:1082` | Separate IPv4/IPv6 DNAT rules |
| System default | `/proc/sys/net/ipv6/bindv6only` | Usually `0` (dual-stack) |
