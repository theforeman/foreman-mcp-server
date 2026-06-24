from unittest.mock import Mock

import pytest
from requests.exceptions import HTTPError

from foreman_mcp_server.tools.call_foreman_api import (
    _normalize_numeric_values,
    _parse_params,
    build_failure_structured_content,
    build_success_structured_content,
)
from foreman_mcp_server.utils.content_utils import derive_legacy_content


class TestParseParams:
    def test_valid_json_object(self):
        result = _parse_params('{"search": "name ~ test", "per_page": 20}')
        assert result == {"search": "name ~ test", "per_page": 20}

    def test_empty_json_object(self):
        result = _parse_params("{}")
        assert result == {}

    def test_float_to_int_normalization(self):
        result = _parse_params('{"id": 3.0, "ratio": 1.5}')
        assert result == {"id": 3, "ratio": 1.5}
        assert isinstance(result["id"], int)
        assert isinstance(result["ratio"], float)

    def test_nested_float_normalization(self):
        result = _parse_params('{"host": {"id": 5.0}, "ids": [1.0, 2.0]}')
        assert result == {"host": {"id": 5}, "ids": [1, 2]}

    def test_invalid_json_raises_value_error(self):
        with pytest.raises(ValueError, match="must be a valid JSON string"):
            _parse_params("not json")

    def test_non_object_json_raises_value_error(self):
        with pytest.raises(ValueError, match="must be a JSON object"):
            _parse_params("[1, 2, 3]")

    def test_none_raises_value_error(self):
        with pytest.raises(ValueError, match="must be a valid JSON string"):
            _parse_params(None)


class TestNormalizeNumericValues:
    def test_whole_float_becomes_int(self):
        assert _normalize_numeric_values(3.0) == 3
        assert isinstance(_normalize_numeric_values(3.0), int)

    def test_fractional_float_stays_float(self):
        assert _normalize_numeric_values(3.5) == 3.5
        assert isinstance(_normalize_numeric_values(3.5), float)

    def test_string_unchanged(self):
        assert _normalize_numeric_values("hello") == "hello"

    def test_int_unchanged(self):
        assert _normalize_numeric_values(3) == 3

    def test_nested_dict(self):
        result = _normalize_numeric_values({"a": 1.0, "b": {"c": 2.0}})
        assert result == {"a": 1, "b": {"c": 2}}

    def test_list(self):
        result = _normalize_numeric_values([1.0, 2.5, "x"])
        assert result == [1, 2.5, "x"]


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
```json
{
  "error": "test error"
}
```
"""
        )
