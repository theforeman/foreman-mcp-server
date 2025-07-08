from unittest.mock import Mock

from requests.exceptions import HTTPError

from foreman_mcp_server.tools.call_foreman_api import (
    build_failure_structured_content,
    build_success_structured_content,
    derive_legacy_content,
)


class TestCallForemanApi:
    def test_build_success_content(self):
        response = "test response"
        expected = {
            "message": "Action 'test_action' on resource 'test_resource' executed successfully.",
            "response": response,
        }
        structured = build_success_structured_content(
            "test_resource", "test_action", response
        )
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Action 'test_action' on resource 'test_resource' executed successfully.

# Response
test response
"""
        )

    def test_build_failure_content(self):
        error = Exception("test error")
        expected = {
            "message": "Failed to execute action 'test_action' on resource 'test_resource'",
            "error": "test error",
        }

        structured = build_failure_structured_content(
            "test_resource", "test_action", error
        )
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Failed to execute action 'test_action' on resource 'test_resource'

# Error
test error
"""
        )

    def test_build_failure_with_http_error(self):
        error = HTTPError("test error", response=Mock(text="<html>test error</html>"))
        expected = {
            "message": "Failed to execute action 'test_action' on resource 'test_resource'",
            "error": "test error",
            "response": "<html>test error</html>",
        }
        structured = build_failure_structured_content(
            "test_resource", "test_action", error
        )
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Failed to execute action 'test_action' on resource 'test_resource'

# Error
test error

# Response
<html>test error</html>
"""
        )

    def test_build_failure_with_http_error_and_json_response(self):
        error = HTTPError("test error", response=Mock(text='{"error": "test error"}'))
        expected = {
            "message": "Failed to execute action 'test_action' on resource 'test_resource'",
            "error": "test error",
            "response": {"error": "test error"},
        }
        structured = build_failure_structured_content(
            "test_resource", "test_action", error
        )
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Failed to execute action 'test_action' on resource 'test_resource'

# Error
test error

# Response
{'error': 'test error'}
"""
        )
