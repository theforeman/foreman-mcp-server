from unittest.mock import Mock

from requests.exceptions import HTTPError

from foreman_mcp_server.tools.remote_execution import (
    format_job_invocation_failure,
    format_job_invocation_success,
)
from foreman_mcp_server.utils.content_utils import derive_legacy_content


class TestTriggerRemoteExecutionJob:
    def test_format_job_invocation_success(self):
        response = {
            "id": 123,
            "description": "Apply errata RHSA-2025:1234",
            "status": 0,
            "status_label": "queued",
            "task": {"id": "abc-123-def"},
            "targeting": {"search_query": "installable_errata = RHSA-2025:1234"},
            "total_hosts_count": 5,
        }

        result = format_job_invocation_success(response)

        assert result.structured_content["message"] == "Remote execution job triggered successfully."
        assert result.structured_content["job_invocation_id"] == 123
        assert result.structured_content["task_id"] == "abc-123-def"
        assert result.structured_content["description"] == "Apply errata RHSA-2025:1234"
        assert result.structured_content["targeting"]["hosts_count"] == 5

    def test_format_job_invocation_success_without_task(self):
        response = {
            "id": 123,
            "description": "Test job",
            "status": 0,
            "status_label": "queued",
            "task": None,
            "targeting": {"search_query": "name ~ test"},
            "total_hosts_count": 1,
        }

        result = format_job_invocation_success(response)

        assert result.structured_content["task_id"] is None

    def test_format_job_invocation_failure(self):
        error = Exception("Connection refused")

        result = format_job_invocation_failure(error)

        assert result.structured_content["message"] == "Failed to trigger remote execution job."
        assert result.structured_content["error"] == "Connection refused"

    def test_format_job_invocation_failure_with_http_error(self):
        error = HTTPError(
            "422 Unprocessable Entity",
            response=Mock(text='{"error": "Job template not found"}'),
        )

        result = format_job_invocation_failure(error)

        assert result.structured_content["message"] == "Failed to trigger remote execution job."
        assert "422 Unprocessable Entity" in result.structured_content["error"]
        assert result.structured_content["response"] == {"error": "Job template not found"}

    def test_format_job_invocation_failure_with_http_error_html_response(self):
        error = HTTPError(
            "500 Internal Server Error",
            response=Mock(text="<html>Internal Error</html>"),
        )

        result = format_job_invocation_failure(error)

        assert result.structured_content["response"] == "<html>Internal Error</html>"


class TestLegacyContentDerivation:
    """Test that structured content can be properly converted to legacy text format."""

    def test_job_invocation_success_legacy_content(self):
        response = {
            "id": 123,
            "task": {"id": "abc-123"},
            "targeting": {"search_query": "name ~ test"},
            "total_hosts_count": 2,
            "status": 0,
            "status_label": "queued",
            "description": "Test job",
        }

        result = format_job_invocation_success(response)
        content = derive_legacy_content(result.structured_content)

        assert "Remote execution job triggered successfully" in content
        assert "123" in content  # job_invocation_id
        assert "abc-123" in content  # task_id
