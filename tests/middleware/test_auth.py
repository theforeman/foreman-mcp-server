import asyncio
from unittest.mock import MagicMock, Mock, patch

import pytest

from foreman_mcp_server.middleware.auth import AuthMiddleware
from foreman_mcp_server.utils.utils import get_foreman_api


def make_http_request(username=None, token=None, session_id=None):
    headers = {}
    if username is not None:
        headers["foreman_username"] = username
    if token is not None:
        headers["foreman_token"] = token
    if session_id is not None:
        headers["mcp-session-id"] = session_id

    request = Mock()
    request.headers.get = lambda key, default=None: headers.get(key, default)
    return request


class TestAuthMiddleware:
    def setup_method(self):
        self.middleware = AuthMiddleware(
            foreman_url="https://foreman.example.com",
            verify_ssl=True,
            foreman_api=None,
        )

    @patch("foreman_mcp_server.middleware.auth.get_http_request")
    @patch("foreman_mcp_server.middleware.auth.apypie.ForemanApi")
    def test_creates_foreman_api_from_headers(
        self, mock_foreman_api, mock_get_http_request
    ):
        mock_get_http_request.return_value = make_http_request(
            username="admin", token="secret-token", session_id="session-1"
        )
        self.middleware.get_foreman_api_from_request()

        mock_foreman_api.assert_called_once_with(
            uri="https://foreman.example.com",
            username="admin",
            password="secret-token",
            verify_ssl=True,
        )

    @patch("foreman_mcp_server.middleware.auth.get_http_request")
    @patch("foreman_mcp_server.middleware.auth.apypie.ForemanApi")
    def test_always_returns_new_instance(self, mock_foreman_api, mock_get_http_request):
        sentinel_1 = object()
        sentinel_2 = object()
        mock_foreman_api.side_effect = [sentinel_1, sentinel_2]

        mock_get_http_request.return_value = make_http_request(
            username="admin", token="token-1", session_id="session-1"
        )
        result_1 = self.middleware.get_foreman_api_from_request()

        mock_get_http_request.return_value = make_http_request(
            username="admin", token="token-2", session_id="session-1"
        )
        result_2 = self.middleware.get_foreman_api_from_request()

        assert result_1 is not result_2
        assert mock_foreman_api.call_count == 2

    @patch("foreman_mcp_server.middleware.auth.get_http_request")
    @pytest.mark.parametrize("username", [None, ""])
    def test_missing_username_raises(self, mock_get_http_request, username):
        mock_get_http_request.return_value = make_http_request(
            username=username, token="token", session_id="session-1"
        )
        with pytest.raises(RuntimeError, match="username and token must be provided"):
            self.middleware.get_foreman_api_from_request()

    @patch("foreman_mcp_server.middleware.auth.get_http_request")
    @pytest.mark.parametrize("token", [None, ""])
    def test_missing_token_raises(self, mock_get_http_request, token):
        mock_get_http_request.return_value = make_http_request(
            username="admin", token=token, session_id="session-1"
        )
        with pytest.raises(RuntimeError, match="username and token must be provided"):
            self.middleware.get_foreman_api_from_request()

    @patch("foreman_mcp_server.middleware.auth.get_http_request")
    def test_stdio_transport_returns_none(self, mock_get_http_request):
        mock_get_http_request.side_effect = RuntimeError("No HTTP context")
        result = self.middleware.get_foreman_api_from_request()
        assert result is None

    def test_prebuilt_foreman_api_stored_in_request_state(self):
        prebuilt = Mock()
        middleware = AuthMiddleware(
            foreman_url="https://foreman.example.com",
            verify_ssl=True,
            foreman_api=prebuilt,
        )
        context = Mock()
        context.fastmcp_context._request_state = {}

        async def call_next(ctx):
            return ctx

        asyncio.run(middleware.on_request(context, call_next))
        assert context.fastmcp_context._request_state["foreman_api"] is prebuilt

    @patch("foreman_mcp_server.middleware.auth.get_http_request")
    @patch("foreman_mcp_server.middleware.auth.apypie.ForemanApi")
    def test_on_request_stores_foreman_api_in_request_state(
        self, mock_foreman_api, mock_get_http_request
    ):
        mock_foreman_api_instance = Mock()
        mock_foreman_api.return_value = mock_foreman_api_instance
        mock_get_http_request.return_value = make_http_request(
            username="admin", token="secret", session_id="session-1"
        )

        context = Mock()
        context.fastmcp_context._request_state = {}

        async def call_next(ctx):
            return ctx

        asyncio.run(self.middleware.on_request(context, call_next))
        assert (
            context.fastmcp_context._request_state["foreman_api"]
            is mock_foreman_api_instance
        )


class TestGetForemanApi:
    def test_reads_from_request_state(self):
        mock_api = Mock()
        ctx = Mock()
        ctx._request_state = {"foreman_api": mock_api}

        result = get_foreman_api(ctx)
        assert result is mock_api

    def test_falls_back_to_attribute_when_request_state_missing(self):
        mock_api = Mock()
        ctx = Mock(spec=[])
        ctx.foreman_api = mock_api

        result = get_foreman_api(ctx)
        assert result is mock_api

    def test_missing_request_state_attribute_does_not_raise(self):
        ctx = MagicMock()
        del ctx._request_state
        ctx.foreman_api = None

        with pytest.raises(RuntimeError, match="Foreman API is not available"):
            get_foreman_api(ctx)

    def test_raises_when_no_foreman_api(self):
        ctx = Mock()
        ctx._request_state = {}
        ctx.foreman_api = None

        with pytest.raises(RuntimeError, match="Foreman API is not available"):
            get_foreman_api(ctx)
