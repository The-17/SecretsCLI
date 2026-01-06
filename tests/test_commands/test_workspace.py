"""
Tests for Workspace Commands

Covers:
- workspace list
- workspace switch (with 'personal' keyword)
- workspace create
- workspace invite
- workspace members
- workspace remove
"""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from pathlib import Path
import json

from secretscli.cli import app
from secretscli.utils.credentials import CredentialsManager
from tests.conftest import make_api_response


runner = CliRunner()


class TestWorkspaceList:
    """Tests for 'workspace list' command."""
    
    def test_list_shows_all_workspaces(self, full_mock_env):
        """All workspaces should be displayed in table."""
        result = runner.invoke(app, ["workspace", "list"])
        
        assert result.exit_code == 0
        assert "Personal Workspace" in result.stdout
        assert "Team Workspace" in result.stdout
    
    def test_list_shows_selected_indicator(self, full_mock_env):
        """Selected workspace should be marked."""
        result = runner.invoke(app, ["workspace", "list"])
        
        assert "(Selected)" in result.stdout


class TestWorkspaceSwitch:
    """Tests for 'workspace switch' command."""
    
    def test_switch_by_name(self, full_mock_env):
        """Switch should update selected_workspace_id."""
        result = runner.invoke(app, ["workspace", "switch", "Team Workspace"])
        
        assert result.exit_code == 0
        assert "Selected workspace" in result.stdout
    
    def test_switch_personal_keyword(self, full_mock_env):
        """'personal' keyword should find personal workspace."""
        # First switch to team
        CredentialsManager.set_selected_workspace("ws-team-456")
        
        result = runner.invoke(app, ["workspace", "switch", "personal"])
        
        assert result.exit_code == 0
        assert "personal" in result.stdout.lower()
    
    def test_switch_already_selected(self, full_mock_env):
        """Should show warning if already selected."""
        # Personal is already selected in fixture
        result = runner.invoke(app, ["workspace", "switch", "Personal Workspace"])
        
        assert "already selected" in result.stdout.lower()
    
    def test_switch_not_found(self, full_mock_env):
        """Should error for non-existent workspace."""
        result = runner.invoke(app, ["workspace", "switch", "NonExistent"])
        
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestWorkspaceCreate:
    """Tests for 'workspace create' command."""
    
    def test_create_calls_api(self, full_mock_env, mock_api, sample_keypair):
        """New workspace should call API."""
        private_key, public_key = sample_keypair
        
        mock_api.return_value = make_api_response(201, {
            "id": "ws-new-789",
            "name": "New Workspace"
        })
        
        with patch.object(CredentialsManager, 'get_public_key', return_value=public_key):
            with patch.object(CredentialsManager, 'get_email', return_value="test@example.com"):
                result = runner.invoke(app, ["workspace", "create", "New Workspace"])
                
                # Should call API
                assert mock_api.called


class TestWorkspaceInvite:
    """Tests for 'workspace invite' command."""
    
    def test_invite_requires_project_workspace(self, temp_project_dir, bypass_auth):
        """Should error if no project workspace set."""
        result = runner.invoke(app, ["workspace", "invite", "user@example.com"])
        
        assert result.exit_code == 1
        assert "No project workspace set" in result.stdout


class TestWorkspaceMembers:
    """Tests for 'workspace members' command."""
    
    def test_members_requires_project_workspace(self, temp_project_dir, bypass_auth):
        """Should error if no project workspace set."""
        result = runner.invoke(app, ["workspace", "members"])
        
        assert result.exit_code == 1
        assert "No project workspace set" in result.stdout


class TestWorkspaceRemove:
    """Tests for 'workspace remove' command."""
    
    def test_remove_requires_project_workspace(self, temp_project_dir, bypass_auth):
        """Should error if no project workspace set."""
        result = runner.invoke(app, ["workspace", "remove", "user@example.com"])
        
        assert result.exit_code == 1
        assert "No project workspace set" in result.stdout
