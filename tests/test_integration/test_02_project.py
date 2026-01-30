"""
Integration Tests - Project Commands

Tests project creation, listing, use, and deletion against real API.
Requires authenticated session from auth tests.
"""
import pytest
import json
from typer.testing import CliRunner

from secretscli.cli import app
from secretscli.utils.credentials import CredentialsManager

from .conftest import TestSession

runner = CliRunner()


@pytest.mark.order(3)
class TestProjectCreate:
    """Test project creation."""
    
    def test_create_project(self, test_home, test_project_dir, unique_project_name):
        """
        Create a new project via CLI.
        """
        result = runner.invoke(app, [
            "project", "create", unique_project_name,
            "-d", "Integration test project"
        ])
        
        assert result.exit_code == 0, f"Failed to create project: {result.stdout}"
        assert unique_project_name in result.stdout
        
        # Track for cleanup
        TestSession.created_projects.append(unique_project_name)
        TestSession.test_project_name = unique_project_name
        
        # Verify project stored in config (immediately after create, in same test)
        config = CredentialsManager.get_project_config()
        assert config is not None
        assert config.get("project_id") is not None
        assert config.get("project_name") == unique_project_name


@pytest.mark.order(4)
class TestProjectList:
    """Test project listing."""
    
    def test_list_shows_created_project(self, test_home):
        """Created project should appear in list."""
        result = runner.invoke(app, ["project", "list"])
        
        assert result.exit_code == 0
        assert TestSession.test_project_name in result.stdout


@pytest.mark.order(5)
class TestProjectUse:
    """Test project use (binding to directory)."""
    
    def test_use_project_binds_to_directory(self, test_home, test_project_dir):
        """
        Use project should bind it to current directory.
        """
        # Create a fresh project for this test
        project_name = f"use-test-{TestSession.test_project_name[-8:]}"
        
        # First create it
        create_result = runner.invoke(app, ["project", "create", project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(project_name)
        
        # Clear local config
        config_file = test_project_dir / ".secretscli" / "project.json"
        config_file.write_text(json.dumps({
            "project_id": None,
            "project_name": None,
            "workspace_id": None
        }))
        
        # Now use it
        result = runner.invoke(app, ["project", "use", project_name])
        
        assert result.exit_code == 0, f"Use failed: {result.stdout}"
        
        # Verify binding
        config = CredentialsManager.get_project_config()
        assert config.get("project_name") == project_name


@pytest.mark.order(10)  # Run after secrets tests
class TestProjectDelete:
    """Test project deletion - runs last."""
    
    def test_delete_project(self, test_home, test_project_dir):
        """
        Delete a test project.
        """
        # Create a project specifically for deletion test
        project_name = f"delete-test-{TestSession.test_project_name[-8:]}"
        
        create_result = runner.invoke(app, ["project", "create", project_name])
        assert create_result.exit_code == 0
        
        # Delete it
        result = runner.invoke(app, ["project", "delete", project_name, "--force"])
        
        assert result.exit_code == 0, f"Delete failed: {result.stdout}"
        assert "deleted" in result.stdout.lower()
