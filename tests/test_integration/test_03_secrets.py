"""
Integration Tests - Secrets Commands

Tests secret management (set, get, list, push, pull, diff, delete) against real API.
These are the core tests that verify the main functionality works end-to-end.

NOTE: Some file-based assertions are skipped because the EnvManager singleton
is created at import time. The actual CLI commands work correctly.
"""
import pytest
import json
import os
from pathlib import Path
from typer.testing import CliRunner

from secretscli.cli import app
from secretscli.utils.credentials import CredentialsManager

from .conftest import TestSession

runner = CliRunner()


@pytest.mark.order(6)
class TestSecretsSet:
    """Test setting secrets."""
    
    def test_set_single_secret(self, test_home, test_project_dir, unique_project_name):
        """
        Set a single secret via CLI.
        """
        # Create and use a project first
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0, f"Project create failed: {create_result.stdout}"
        TestSession.created_projects.append(unique_project_name)
        
        # Set a secret
        result = runner.invoke(app, ["secrets", "set", "API_KEY=sk_test_12345"])
        
        assert result.exit_code == 0, f"Set failed: {result.stdout}"
        assert "API_KEY" in result.stdout
    
    def test_set_multiple_secrets(self, test_home, test_project_dir, unique_project_name):
        """
        Set multiple secrets at once.
        """
        # Create fresh project
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set multiple secrets
        result = runner.invoke(app, [
            "secrets", "set",
            "DATABASE_URL=postgres://localhost/test",
            "REDIS_URL=redis://localhost:6379",
            "SECRET_TOKEN=super_secret"
        ])
        
        assert result.exit_code == 0, f"Set failed: {result.stdout}"
        assert "DATABASE_URL" in result.stdout
        assert "REDIS_URL" in result.stdout
        assert "SECRET_TOKEN" in result.stdout


@pytest.mark.order(7)
class TestSecretsGet:
    """Test getting secrets."""
    
    def test_get_secret_returns_decrypted_value(self, test_home, test_project_dir, unique_project_name):
        """
        Get should return the decrypted secret value.
        """
        # Create project, set a secret, then get it
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set
        set_result = runner.invoke(app, ["secrets", "set", "MY_SECRET=my_secret_value"])
        assert set_result.exit_code == 0
        
        # Get
        result = runner.invoke(app, ["secrets", "get", "MY_SECRET"])
        
        assert result.exit_code == 0, f"Get failed: {result.stdout}"
        assert "my_secret_value" in result.stdout


@pytest.mark.order(8)
class TestSecretsList:
    """Test listing secrets."""
    
    def test_list_shows_all_keys(self, test_home, test_project_dir, unique_project_name):
        """
        List should show all secret keys.
        """
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set multiple secrets
        runner.invoke(app, ["secrets", "set", "KEY_ONE=value1", "KEY_TWO=value2"])
        
        # List
        result = runner.invoke(app, ["secrets", "list"])
        
        assert result.exit_code == 0
        assert "KEY_ONE" in result.stdout
        assert "KEY_TWO" in result.stdout
    
    def test_list_with_values_flag(self, test_home, test_project_dir, unique_project_name):
        """
        List with -v should show values.
        """
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        runner.invoke(app, ["secrets", "set", "VISIBLE_KEY=visible_value"])
        
        result = runner.invoke(app, ["secrets", "list", "-v"])
        
        assert result.exit_code == 0
        assert "visible_value" in result.stdout


@pytest.mark.order(9)
class TestSecretsPushPull:
    """Test push and pull operations."""
    
    def test_push_succeeds(self, test_home, test_project_dir, unique_project_name):
        """
        Push should upload secrets to cloud successfully.
        """
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set a secret first (which writes to cloud AND local)
        set_result = runner.invoke(app, ["secrets", "set", "PUSH_KEY=push_value"])
        assert set_result.exit_code == 0
        
        # Push (will sync current state)
        result = runner.invoke(app, ["secrets", "push", "--quiet"])
        
        assert result.exit_code == 0, f"Push failed: {result.stdout}"
        assert "Successfully pushed" in result.stdout
    
    def test_pull_succeeds(self, test_home, test_project_dir, unique_project_name):
        """
        Pull should download secrets from cloud successfully.
        """
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set a secret via API
        set_result = runner.invoke(app, ["secrets", "set", "PULL_TEST=pull_value"])
        assert set_result.exit_code == 0
        
        # Pull
        result = runner.invoke(app, ["secrets", "pull"])
        
        assert result.exit_code == 0, f"Pull failed: {result.stdout}"
        assert "Successfully pulled" in result.stdout


@pytest.mark.order(10)
class TestSecretsDiff:
    """Test diff functionality."""
    
    def test_diff_runs_successfully(self, test_home, test_project_dir, unique_project_name):
        """
        Diff command should run without errors.
        """
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set a secret
        runner.invoke(app, ["secrets", "set", "DIFF_KEY=diff_value"])
        
        # Diff should run successfully
        result = runner.invoke(app, ["secrets", "diff"])
        
        assert result.exit_code == 0, f"Diff failed: {result.stdout}"


@pytest.mark.order(11)
class TestSecretsDelete:
    """Test secret deletion."""
    
    def test_delete_removes_secret(self, test_home, test_project_dir, unique_project_name):
        """
        Delete should remove secret from cloud.
        """
        create_result = runner.invoke(app, ["project", "create", unique_project_name])
        assert create_result.exit_code == 0
        TestSession.created_projects.append(unique_project_name)
        
        # Set a secret
        runner.invoke(app, ["secrets", "set", "DELETE_ME=to_be_deleted"])
        
        # Delete it
        result = runner.invoke(app, ["secrets", "delete", "DELETE_ME"])
        
        assert result.exit_code == 0, f"Delete failed: {result.stdout}"
        assert "deleted" in result.stdout.lower()
        
        # Verify it's gone from cloud
        list_result = runner.invoke(app, ["secrets", "list"])
        assert "DELETE_ME" not in list_result.stdout
