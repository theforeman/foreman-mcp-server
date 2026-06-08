from unittest.mock import Mock, patch

import pytest

from foreman_mcp_server.middleware.auth import AuthMiddleware


def make_context(username=None, token=None, session_id=None):
    headers = {}
    if username is not None:
        headers["foreman_username"] = username
    if token is not None:
        headers["foreman_token"] = token
    if session_id is not None:
        headers["mcp-session-id"] = session_id

    context = Mock()
    context.fastmcp_context.request_context.request.headers.get = (
        lambda key, default=None: headers.get(key, default)
    )
    return context


class TestAuthMiddleware:
    def setup_method(self):
        self.middleware = AuthMiddleware(
            foreman_url="https://foreman.example.com",
            verify_ssl=True,
            foreman_api=None,
        )

    @patch("foreman_mcp_server.middleware.auth.apypie.ForemanApi")
    def test_creates_foreman_api_from_headers(self, mock_foreman_api):
        context = make_context(
            username="admin", token="secret-token", session_id="session-1"
        )
        self.middleware.get_foreman_api_from_request(context)

        mock_foreman_api.assert_called_once_with(
            uri="https://foreman.example.com",
            username="admin",
            password="secret-token",
            verify_ssl=True,
        )

    @patch("foreman_mcp_server.middleware.auth.apypie.ForemanApi")
    @pytest.mark.parametrize(
        "token_1, token_2",
        [
            ("real-token", "fake-token"),
            ("same-token", "same-token"),
        ],
    )
    def test_always_returns_new_instance(
        self, mock_foreman_api, token_1, token_2
    ):
        sentinel_1 = object()
        sentinel_2 = object()
        mock_foreman_api.side_effect = [sentinel_1, sentinel_2]

        context_1 = make_context(
            username="admin", token=token_1, session_id="session-1"
        )
        context_2 = make_context(
            username="admin", token=token_2, session_id="session-1"
        )

        result_1 = self.middleware.get_foreman_api_from_request(context_1)
        result_2 = self.middleware.get_foreman_api_from_request(context_2)

        assert result_1 is not result_2
        assert mock_foreman_api.call_count == 2

    @pytest.mark.parametrize("username", [None, ""])
    def test_missing_username_raises(self, username):
        context = make_context(username=username, token="token", session_id="session-1")
        with pytest.raises(RuntimeError, match="username and token must be provided"):
            self.middleware.get_foreman_api_from_request(context)

    @pytest.mark.parametrize("token", [None, ""])
    def test_missing_token_raises(self, token):
        context = make_context(username="admin", token=token, session_id="session-1")
        with pytest.raises(RuntimeError, match="username and token must be provided"):
            self.middleware.get_foreman_api_from_request(context)

    def test_prebuilt_foreman_api_used_when_available(self):
        prebuilt = Mock()
        middleware = AuthMiddleware(
            foreman_url="https://foreman.example.com",
            verify_ssl=True,
            foreman_api=prebuilt,
        )
        context = make_context()

        async def call_next(ctx):
            return ctx

        import asyncio

        asyncio.run(middleware.on_request(context, call_next))
        assert context.fastmcp_context.foreman_api == prebuilt
