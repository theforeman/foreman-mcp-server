from foreman_mcp_server.tools.call_hammer_commands import (
    build_failure_structured_content,
    build_success_structured_content,
)
from foreman_mcp_server.utils.content_utils import derive_legacy_content


class TestCallHammerCommands:
    def test_build_success_content(self):
        command = "host list"
        output = "host1.example.com\nhost2.example.com\n"
        returncode = 0
        expected = {
            "message": f"Hammer command executed successfully: hammer {command}",
            "command": f"hammer {command}",
            "output": output,
            "returncode": returncode,
        }
        structured = build_success_structured_content(command, output, returncode)
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Hammer command executed successfully: hammer host list

# Command
hammer host list

# Output
host1.example.com
host2.example.com


# Returncode
0
"""
        )

    def test_build_failure_content(self):
        command = "host delete --id 999"
        output = ""
        error = "Error: Host not found\n"
        returncode = 1
        expected = {
            "message": f"Hammer command failed: hammer {command}",
            "command": f"hammer {command}",
            "output": output,
            "error": error,
            "returncode": returncode,
        }

        structured = build_failure_structured_content(
            command, output, error, returncode
        )
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Hammer command failed: hammer host delete --id 999

# Command
hammer host delete --id 999

# Output


# Error
Error: Host not found


# Returncode
1
"""
        )

    def test_build_failure_content_with_output_and_error(self):
        command = "host create --name test"
        output = "Creating host...\n"
        error = "Error: Missing required parameter --organization-id\n"
        returncode = 65
        expected = {
            "message": f"Hammer command failed: hammer {command}",
            "command": f"hammer {command}",
            "output": output,
            "error": error,
            "returncode": returncode,
        }

        structured = build_failure_structured_content(
            command, output, error, returncode
        )
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Hammer command failed: hammer host create --name test

# Command
hammer host create --name test

# Output
Creating host...


# Error
Error: Missing required parameter --organization-id


# Returncode
65
"""
        )

    def test_build_success_content_with_empty_output(self):
        command = "organization delete --id 1"
        output = ""
        returncode = 0
        expected = {
            "message": f"Hammer command executed successfully: hammer {command}",
            "command": f"hammer {command}",
            "output": output,
            "returncode": returncode,
        }
        structured = build_success_structured_content(command, output, returncode)
        assert structured == expected

        content = derive_legacy_content(structured)
        assert (
            content
            == """# Message
Hammer command executed successfully: hammer organization delete --id 1

# Command
hammer organization delete --id 1

# Output


# Returncode
0
"""
        )
