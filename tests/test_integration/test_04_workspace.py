"""
Integration Tests - Workspace Commands

Tests workspace listing, switching, and creation against real API.
"""
import pytest
from typer.testing import CliRunner

from secretscli.cli import app
from secretscli.utils.credentials import CredentialsManager

from .conftest import TestSession

runner = CliRunner()


@pytest.mark.order(12)
class TestWorkspaceList:
    """Test workspace listing."""
    
    def test_list_shows_personal_workspace(self, test_home):
        """
        List should show at least personal workspace.
        """
        result = runner.invoke(app, ["workspace", "list"])
        
        assert result.exit_code == 0
        # Should have at least one workspace
        assert "Personal" in result.stdout or "personal" in result.stdout.lower()
    
    def test_list_shows_selected_indicator(self, test_home):
        """
        Selected workspace should be marked.
        """
        result = runner.invoke(app, ["workspace", "list"])
        
        assert result.exit_code == 0
        assert "(Selected)" in result.stdout


@pytest.mark.order(13)
class TestWorkspaceSwitch:
    """Test workspace switching."""
    
    def test_switch_personal_keyword(self, test_home):
        """
        'personal' keyword should select personal workspace.
        """
        result = runner.invoke(app, ["workspace", "switch", "personal"])
        
        # Either succeeds or says already selected
        assert result.exit_code == 0
        assert "personal" in result.stdout.lower() or "already" in result.stdout.lower()
    
    def test_switch_nonexistent_fails(self, test_home):
        """
        Switching to nonexistent workspace should fail.
        """
        result = runner.invoke(app, ["workspace", "switch", "NonExistentWorkspace123"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


@pytest.mark.order(14)
class TestWorkspaceCreate:
    """Test workspace creation."""
    
    def test_create_workspace(self, test_home):
        """
        Create a new team workspace.
        """
        import uuid
        workspace_name = f"Test Team {uuid.uuid4().hex[:6]}"
        
        result = runner.invoke(app, ["workspace", "create", workspace_name])
        
        assert result.exit_code == 0, f"Create failed: {result.stdout}"
        assert workspace_name in result.stdout or "created" in result.stdout.lower()
