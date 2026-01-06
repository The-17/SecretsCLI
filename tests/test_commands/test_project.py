"""
Tests for Project Commands

Covers:
- project create
- project list (grouped by workspace)
- project use
- project update
- project delete
- project invite
"""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from pathlib import Path
import json
import base64

from secretscli.cli import app
from secretscli.utils.credentials import CredentialsManager
from tests.conftest import make_api_response


runner = CliRunner()


class TestProjectCreate:
    """Tests for 'project create' command."""
    
    def test_create_calls_api(self, full_mock_env, mock_api, sample_workspace_key):
        """Project should call API with selected workspace."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        
        mock_api.return_value = make_api_response(201, {
            "id": "proj-new-123",
            "name": "new-project",
            "workspace_id": "ws-personal-123"
        })
        
        result = runner.invoke(app, ["project", "create", "new-project"])
        
        # API should have been called
        assert mock_api.called
    
    def test_create_requires_name(self, full_mock_env, mock_api):
        """Should error when name not provided."""
        result = runner.invoke(app, ["project", "create"])
        
        # Typer should show usage error
        assert result.exit_code != 0


class TestProjectList:
    """Tests for 'project list' command."""
    
    def test_list_calls_api(self, full_mock_env, mock_api):
        """Projects should be fetched from API."""
        mock_api.return_value = make_api_response(200, [
            {"id": "proj-1", "name": "my-api", "workspace_id": "ws-personal-123"},
            {"id": "proj-2", "name": "team-app", "workspace_id": "ws-team-456"}
        ])
        
        result = runner.invoke(app, ["project", "list"])
        
        assert mock_api.called
    
    def test_list_empty_projects(self, full_mock_env, mock_api):
        """Should show message when no projects."""
        mock_api.return_value = make_api_response(200, [])
        
        result = runner.invoke(app, ["project", "list"])
        
        assert "No projects found" in result.stdout


class TestProjectUse:
    """Tests for 'project use' command."""
    
    def test_use_calls_api(self, full_mock_env, mock_api):
        """project use should fetch project details from API."""
        mock_api.return_value = make_api_response(200, {
            "id": "proj-123",
            "name": "my-api",
            "description": "My API",
            "workspace_id": "ws-personal-123"
        })
        
        result = runner.invoke(app, ["project", "use", "my-api"])
        
        assert mock_api.called
    
    def test_use_project_not_found(self, full_mock_env, mock_api):
        """Should error for non-existent project."""
        mock_api.return_value = make_api_response(404, error="Project not found")
        
        result = runner.invoke(app, ["project", "use", "nonexistent"])
        
        assert result.exit_code == 1


class TestProjectUpdate:
    """Tests for 'project update' command."""
    
    def test_update_calls_api(self, full_mock_env, mock_api, temp_project_dir):
        """Project should be updated via API."""
        # Set up existing project
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="old-name",
            workspace_id="ws-123",
            workspace_name="Test",
            workspace_key="key"
        )
        
        mock_api.return_value = make_api_response(200, {
            "id": "proj-123",
            "name": "new-name"
        })
        
        result = runner.invoke(app, ["project", "update", "old-name", "--name", "new-name"])
        
        # Should call API (may have other requirements)
        assert mock_api.called


class TestProjectDelete:
    """Tests for 'project delete' command."""
    
    def test_delete_with_force_calls_api(self, full_mock_env, mock_api, temp_project_dir):
        """Project should be deleted with --force flag."""
        mock_api.return_value = make_api_response(200, {})
        
        result = runner.invoke(app, ["project", "delete", "test-project", "--force"])
        
        # Should call API
        assert mock_api.called


class TestProjectInvite:
    """Tests for 'project invite' command."""
    
    def test_invite_requires_project(self, temp_project_dir):
        """Should error if no project configured."""
        result = runner.invoke(app, ["project", "invite", "user@example.com"])
        
        assert result.exit_code == 1
