"""
Tests for Secrets Commands

Covers:
- secrets set (encryption)
- secrets get (decryption)
- secrets list
- secrets delete
- secrets push (from .env)
- secrets pull (to .env)
"""
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from pathlib import Path
import json
import base64

from secretscli.cli import app
from secretscli.utils.credentials import CredentialsManager
from secretscli.encryption import EncryptionService
from tests.conftest import make_api_response


runner = CliRunner()


class TestSecretsSet:
    """Tests for 'secrets set' command."""
    
    def test_set_requires_project(self, temp_project_dir, bypass_auth):
        """Should error if no project configured."""
        result = runner.invoke(app, ["secrets", "set", "API_KEY=secret_value"])
        
        # Should error due to no project/workspace key
        assert result.exit_code == 1
    
    def test_set_with_project_calls_api(self, full_mock_env, mock_api, sample_workspace_key):
        """With project configured, should call API."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-personal-123",
            workspace_name="Personal",
            workspace_key=key_b64
        )
        
        mock_api.return_value = make_api_response(201, {"key": "API_KEY"})
        
        # Note: secrets set uses KEY=VALUE format
        result = runner.invoke(app, ["secrets", "set", "API_KEY=secret_value"])
        
        # API should have been called
        assert mock_api.called


class TestSecretsGet:
    """Tests for 'secrets get' command."""
    
    def test_get_calls_api(self, full_mock_env, mock_api, sample_workspace_key):
        """Should call API to get secret."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-personal-123",
            workspace_name="Personal",
            workspace_key=key_b64
        )
        
        # Encrypt a test value
        encrypted = EncryptionService.encrypt_secret("decrypted_value", sample_workspace_key)
        mock_api.return_value = make_api_response(200, {"key": "API_KEY", "value": encrypted})
        
        result = runner.invoke(app, ["secrets", "get", "API_KEY"])
        
        # API should have been called
        assert mock_api.called


class TestSecretsList:
    """Tests for 'secrets list' command."""
    
    def test_list_calls_api(self, full_mock_env, mock_api, sample_workspace_key):
        """Should call API to list secrets."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-personal-123",
            workspace_name="Personal",
            workspace_key=key_b64
        )
        
        mock_api.return_value = make_api_response(200, [
            {"key": "API_KEY", "value": "encrypted1"},
            {"key": "DATABASE_URL", "value": "encrypted2"}
        ])
        
        result = runner.invoke(app, ["secrets", "list"])
        
        # API should have been called
        assert mock_api.called


class TestSecretsPush:
    """Tests for 'secrets push' command."""
    
    def test_push_calls_api(self, full_mock_env, mock_api, sample_workspace_key, temp_env_file):
        """Should read .env and call API."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-personal-123",
            workspace_name="Personal",
            workspace_key=key_b64
        )
        
        mock_api.return_value = make_api_response(200, {})
        
        result = runner.invoke(app, ["secrets", "push"])
        
        # API should have been called
        assert mock_api.called


class TestSecretsPull:
    """Tests for 'secrets pull' command."""
    
    def test_pull_calls_api(self, full_mock_env, mock_api, sample_workspace_key):
        """Should call API to get secrets."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-personal-123",
            workspace_name="Personal",
            workspace_key=key_b64
        )
        
        mock_api.return_value = make_api_response(200, [])
        
        result = runner.invoke(app, ["secrets", "pull"])
        
        # API should have been called
        assert mock_api.called


class TestSecretsDelete:
    """Tests for 'secrets delete' command."""
    
    def test_delete_requires_key_argument(self):
        """Should require secret key argument."""
        result = runner.invoke(app, ["secrets", "delete"])
        
        # Missing argument should error
        assert result.exit_code != 0
