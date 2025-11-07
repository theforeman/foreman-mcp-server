from foreman_mcp_server.utils.hammer_utils import (
    organization_info_command,
    organization_list_command,
)


class TestHammerOrganizationCommands:
    def test_organization_list_command(self):
        """Test organization list command builder returns correct command."""
        command = organization_list_command()
        expected = "organization list"
        assert command == expected

    def test_organization_info_command(self):
        """Test organization info command builder with simple name."""
        command = organization_info_command("Default Organization")
        expected = 'organization info --name "Default Organization"'
        assert command == expected

    def test_organization_info_command_with_simple_name(self):
        """Test organization info command builder with single word name."""
        command = organization_info_command("TestOrg")
        expected = 'organization info --name "TestOrg"'
        assert command == expected

    def test_organization_info_command_with_spaces(self):
        """Test organization info command builder handles names with spaces."""
        command = organization_info_command("My Test Organization")
        expected = 'organization info --name "My Test Organization"'
        assert command == expected

    def test_organization_info_command_with_special_chars(self):
        """Test organization info command builder with special characters."""
        command = organization_info_command("Org-123_Test")
        expected = 'organization info --name "Org-123_Test"'
        assert command == expected
