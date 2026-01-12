from unittest.mock import Mock

from requests.exceptions import HTTPError

from foreman_mcp_server.tools.tasks import (
    format_poll_failure,
    format_poll_success,
    format_poll_timeout,
)
from foreman_mcp_server.utils.content_utils import derive_legacy_content


class TestPollTask:
    def test_format_poll_success(self):
        response = {
            "id": "abc-123-def",
            "state": "stopped",
            "result": "success",
            "started_at": "2025-01-12T10:00:00Z",
            "ended_at": "2025-01-12T10:01:30Z",
            "duration": "1.5 minutes",
            "progress": 1.0,
            "humanized": {"output": "5 hosts, 5 successful"},
        }

        result = format_poll_success(response, elapsed=90)

        assert "completed with state 'stopped'" in result.structured_content["message"]
        assert "90 seconds" in result.structured_content["message"]
        assert result.structured_content["task_id"] == "abc-123-def"
        assert result.structured_content["state"] == "stopped"
        assert result.structured_content["result"] == "success"
        assert result.structured_content["humanized_result"] == "5 hosts, 5 successful"

    def test_format_poll_success_without_humanized(self):
        response = {
            "id": "abc-123-def",
            "state": "stopped",
            "result": "success",
            "started_at": "2025-01-12T10:00:00Z",
            "ended_at": "2025-01-12T10:01:30Z",
            "duration": "1.5 minutes",
            "progress": 1.0,
            "humanized": None,
        }

        result = format_poll_success(response, elapsed=90)

        assert result.structured_content["humanized_result"] is None

    def test_format_poll_timeout(self):
        last_response = {
            "state": "running",
            "progress": 0.5,
        }

        result = format_poll_timeout(
            "abc-123-def", timeout=300, last_response=last_response
        )

        assert (
            "Timeout reached after 300 seconds" in result.structured_content["message"]
        )
        assert result.structured_content["task_id"] == "abc-123-def"
        assert result.structured_content["state"] == "running"
        assert result.structured_content["progress"] == 0.5
        assert "poll_task" in result.structured_content["suggestion"]

    def test_format_poll_failure(self):
        error = Exception("Task not found")

        result = format_poll_failure("abc-123-def", error)

        assert "Failed to poll task" in result.structured_content["message"]
        assert result.structured_content["error"] == "Task not found"

    def test_format_poll_failure_with_http_error(self):
        error = HTTPError(
            "404 Not Found",
            response=Mock(text='{"error": "Task with id abc-123-def not found"}'),
        )

        result = format_poll_failure("abc-123-def", error)

        assert result.structured_content["response"] == {
            "error": "Task with id abc-123-def not found"
        }


class TestLegacyContentDerivation:
    """Test that structured content can be properly converted to legacy text format."""

    def test_poll_success_legacy_content(self):
        response = {
            "id": "task-123",
            "state": "stopped",
            "result": "success",
            "started_at": "2025-01-12T10:00:00Z",
            "ended_at": "2025-01-12T10:01:00Z",
            "duration": "60 seconds",
            "progress": 1.0,
            "humanized": {"output": "All hosts succeeded"},
        }

        result = format_poll_success(response, elapsed=60)
        content = derive_legacy_content(result.structured_content)

        assert "stopped" in content
        assert "success" in content
        assert "task-123" in content
