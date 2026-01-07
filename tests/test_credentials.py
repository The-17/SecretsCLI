"""
Tests for CredentialsManager

Covers:
- Token storage and retrieval
- Keypair management
- Workspace key caching
- Project configuration
- Selected workspace operations

Note: These tests use isolated temp directories to avoid polluting real config.
"""
import pytest
import json
import base64
from pathlib import Path
from unittest.mock import patch, MagicMock

from secretscli.utils.credentials import CredentialsManager


class TestKeypairManagement:
    """Tests for X25519 keypair storage in keychain."""
    
    def test_store_keypair_succeeds(self, mock_keyring, sample_keypair):
        """Keypair should be stored in keyring."""
        private_key, public_key = sample_keypair
        email = "test@example.com"
        
        result = CredentialsManager.store_keypair(email, private_key, public_key)
        
        assert result is True
        # Keyring should have entries (actual key format depends on implementation)
        assert len(mock_keyring) >= 2
    
    def test_get_public_key(self, mock_keyring, sample_keypair):
        """Public key should be retrieved correctly."""
        private_key, public_key = sample_keypair
        email = "test@example.com"
        
        CredentialsManager.store_keypair(email, private_key, public_key)
        retrieved = CredentialsManager.get_public_key(email)
        
        assert retrieved == public_key


class TestWorkspaceCaching:
    """Tests for global workspace key caching."""
    
    def test_store_and_get_workspace_keys(self, temp_home, sample_workspaces):
        """Workspaces should be stored and retrieved from global config."""
        CredentialsManager.store_workspace_keys(sample_workspaces)
        retrieved = CredentialsManager.get_workspace_keys()
        
        assert "ws-personal-123" in retrieved
        assert retrieved["ws-personal-123"]["name"] == "Personal Workspace"
    
    def test_get_workspace_by_id(self, temp_home, sample_workspaces):
        """Single workspace should be retrievable by ID."""
        CredentialsManager.store_workspace_keys(sample_workspaces)
        
        ws = CredentialsManager.get_workspace("ws-personal-123")
        
        assert ws["name"] == "Personal Workspace"
        assert ws["type"] == "personal"
    
    def test_get_workspace_not_found(self, temp_home, sample_workspaces):
        """Should return empty dict for non-existent workspace."""
        CredentialsManager.store_workspace_keys(sample_workspaces)
        
        ws = CredentialsManager.get_workspace("non-existent-id")
        
        assert ws == {}


class TestSelectedWorkspace:
    """Tests for selected workspace (for new projects)."""
    
    def test_set_and_get_selected_workspace(self, temp_home):
        """Selected workspace should be stored and retrieved from global config."""
        CredentialsManager.set_selected_workspace("ws-team-456")
        
        result = CredentialsManager.get_selected_workspace_id()
        
        assert result == "ws-team-456"


class TestProjectConfig:
    """Tests for project-level configuration."""
    
    def test_config_project(self, temp_project_dir):
        """Project config should be created correctly."""
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="my-project",
            description="A test project",
            environment="production",
            workspace_id="ws-123",
            workspace_name="My Workspace"
        )
        
        config = CredentialsManager.get_project_config()
        
        assert config["project_id"] == "proj-123"
        assert config["project_name"] == "my-project"
        assert config["workspace_id"] == "ws-123"
    
    def test_update_project_config(self, temp_project_dir):
        """Partial config update should preserve other fields."""
        # First set up initial config
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="my-project",
            workspace_id="ws-123",
            workspace_name="Workspace"
        )
        
        # Update only one field
        CredentialsManager.update_project_config(last_pull="2025-01-01T00:00:00Z")
        
        config = CredentialsManager.get_project_config()
        
        assert config["project_id"] == "proj-123"  # Preserved
        assert config["workspace_id"] == "ws-123"  # Preserved
        assert config["last_pull"] == "2025-01-01T00:00:00Z"  # Updated
    
    def test_get_project_workspace_id(self, temp_project_dir):
        """Project workspace ID should be retrieved from project.json."""
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-project-789",
            workspace_name="Test"
        )
        
        result = CredentialsManager.get_project_workspace_id()
        
        assert result == "ws-project-789"
    
    def test_get_project_workspace_key(self, temp_home, temp_project_dir, sample_workspace_key):
        """Project workspace key should be fetched from global config via workspace_id."""
        key_b64 = base64.b64encode(sample_workspace_key).decode()
        
        # Store workspace key in global config
        CredentialsManager.store_workspace_keys({
            "ws-123": {
                "name": "Test Workspace",
                "key": key_b64,
                "role": "owner",
                "type": "personal"
            }
        })
        
        # Configure project with workspace_id pointing to that workspace
        CredentialsManager.config_project(
            project_id="proj-123",
            project_name="test",
            workspace_id="ws-123",
            workspace_name="Test"
        )
        
        result = CredentialsManager.get_project_workspace_key()
        
        assert result == sample_workspace_key
