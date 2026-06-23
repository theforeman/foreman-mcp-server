import logging

from fastmcp.server.dependencies import get_http_request
from fastmcp.server.middleware import Middleware, MiddlewareContext

_SAFE_HEADERS = frozenset(
    {
        "accept",
        "accept-encoding",
        "accept-language",
        "cache-control",
        "connection",
        "content-length",
        "content-type",
        "foreman_username",
        "host",
        "mcp-session-id",
        "user-agent",
    }
)


class LoggingMiddleware(Middleware):
    """Middleware that logs all MCP operations."""

    def __init__(
        self,
    ):
        self.logger = logging.getLogger("foreman_mcp_server")

    async def on_message(self, context: MiddlewareContext, call_next):
        if context.fastmcp_context:
            try:
                if context.source == "client":
                    self._log_client_info(context.fastmcp_context)
            except Exception:
                self.logger.debug("Failed to log client info", exc_info=True)
        return await call_next(context)

    def _log_client_info(self, fastmcp_context):
        try:
            request = get_http_request()
        except RuntimeError:
            request = None
        if request is not None:
            if request.client:
                self.logger.debug(
                    f"  Client host: {request.client.host}:{request.client.port}"
                )
            self.logger.debug(
                f"  Client headers: {self._sanitize_headers(request.headers)}"
            )
        self.logger.debug(f"  Client ID: {fastmcp_context.client_id}")
        if fastmcp_context.request_context:
            self.logger.debug(
                f"  Client params: {fastmcp_context.request_context.session.client_params}"
            )

    def _sanitize_headers(self, headers):
        """Sanitize headers to avoid logging sensitive information.

        Only headers in _SAFE_HEADERS have their values logged.
        All other header values are masked, though keys are always visible.
        """
        return {
            key: value if key.lower() in _SAFE_HEADERS else "******"
            for key, value in headers.items()
        }
