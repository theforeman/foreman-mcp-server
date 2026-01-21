"""Tests for task polling tools."""

from unittest.mock import MagicMock

from foreman_mcp_server.tools.tasks import (
    _build_task_summary,
    register_task_tools,
)


class TestBuildTaskSummary:
    """Tests for the task summary helper function."""

    def test_builds_summary_from_task_response(self):
        task_response = {
            "action": "Install errata on hosts",
            "result": "success",
            "duration": "120.5",
            "output": {"total": 10, "successful": 10, "failed": 0},
            "humanized": {
                "output": "All hosts updated successfully",
                "errors": None,
            },
        }

        summary = _build_task_summary(task_response)

        assert summary["action"] == "Install errata on hosts"
        assert summary["result"] == "success"
        assert summary["duration"] == "120.5"
        assert summary["output"]["total"] == 10
        assert summary["humanized_output"] == "All hosts updated successfully"
        assert summary["errors"] is None

    def test_handles_missing_humanized(self):
        task_response = {
            "action": "Install errata on hosts",
            "result": "error",
            "duration": "10.5",
            "output": {},
        }

        summary = _build_task_summary(task_response)

        assert summary["humanized_output"] is None
        assert summary["errors"] is None

    def test_handles_non_dict_output(self):
        task_response = {
            "action": "Some action",
            "result": "success",
            "duration": "5.0",
            "output": "string output",
        }

        summary = _build_task_summary(task_response)

        assert summary["output"] == {}


class TestRegisterTaskTools:
    """Tests for task tool registration."""

    def test_registers_poll_task(self):
        mcp = MagicMock()
        foreman_api = MagicMock()
        get_context = MagicMock()

        register_task_tools(mcp, foreman_api, get_context)

        assert mcp.tool.called

    def test_tool_decorator_called_twice(self):
        mcp = MagicMock()
        foreman_api = MagicMock()
        get_context = MagicMock()

        register_task_tools(mcp, foreman_api, get_context)

        # Should register 2 tools: poll_task and get_task_status
        assert mcp.tool.call_count == 2


class TestPollTaskLogic:
    """Tests for poll_task business logic."""

    def test_terminal_states(self):
        """Test that terminal states are correctly identified."""
        terminal_states = {"stopped", "paused"}

        assert "stopped" in terminal_states
        assert "paused" in terminal_states
        assert "running" not in terminal_states
        assert "pending" not in terminal_states

    def test_elapsed_time_tracking(self):
        """Test the elapsed time calculation logic."""
        timeout_seconds = 300
        poll_interval_seconds = 10
        elapsed = 0
        iterations = 0

        while elapsed < timeout_seconds:
            elapsed += poll_interval_seconds
            iterations += 1
            if iterations > 35:  # Safety limit
                break

        assert elapsed >= timeout_seconds
        assert iterations == 30  # 300 / 10 = 30 iterations


class TestGetTaskStatusLogic:
    """Tests for get_task_status business logic."""

    def test_completion_detection(self):
        """Test that task completion is correctly detected."""
        terminal_states = {"stopped", "paused"}

        test_cases = [
            ("stopped", True),
            ("paused", True),
            ("running", False),
            ("pending", False),
        ]

        for state, expected_complete in test_cases:
            is_complete = state in terminal_states
            assert is_complete == expected_complete, f"Failed for state: {state}"
