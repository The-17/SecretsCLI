"""
Tests for Authentication

Covers:
- Login flow
- Signup flow
- Workspace caching on login
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import base64

from secretscli.utils.credentials import CredentialsManager
from secretscli.encryption import EncryptionService
from cryptography.fernet import Fernet


class TestLogin:
    """Tests for login functionality."""
    
    def test_login_caches_workspaces(self, temp_home, sample_keypair, sample_workspace_key):
        """Login should cache all workspace keys globally."""
        private_key, public_key = sample_keypair
        
        # Create encrypted workspace key for API response
        encrypted_ws_key = EncryptionService.encrypt_for_user(public_key, sample_workspace_key)
        
        workspaces_response = [{
            "id": "ws-123",
            "name": "Test Workspace",
            "encrypted_workspace_key": base64.b64encode(encrypted_ws_key).decode(),
            "role": "owner",
            "type": "personal"
        }]
        
        # Simulate login processing
        workspace_cache = {}
        for ws in workspaces_response:
            encrypted = base64.b64decode(ws["encrypted_workspace_key"])
            decrypted = EncryptionService.decrypt_from_user(private_key, encrypted)
            workspace_cache[ws["id"]] = {
                "name": ws["name"],
                "key": base64.b64encode(decrypted).decode(),
                "role": ws["role"],
                "type": ws["type"]
            }
        
        CredentialsManager.store_workspace_keys(workspace_cache)
        
        # Verify caching worked
        cached = CredentialsManager.get_workspace_keys()
        assert "ws-123" in cached
        assert cached["ws-123"]["name"] == "Test Workspace"
    
    def test_login_sets_selected_workspace(self, temp_home, sample_workspaces):
        """Login should set personal workspace as selected."""
        CredentialsManager.store_workspace_keys(sample_workspaces)
        
        # Simulate the login logic that sets selected workspace
        for ws_id, ws in sample_workspaces.items():
            if ws.get("type") == "personal":
                CredentialsManager.set_selected_workspace(ws_id)
                break
        
        selected = CredentialsManager.get_selected_workspace_id()
        assert selected == "ws-personal-123"


class TestSignup:
    """Tests for signup functionality."""
    
    def test_setup_user_generates_valid_keys(self):
        """Signup should generate valid keypair."""
        password = "secure_password_123"
        
        # Generate keypair
        private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(password)
        
        # Keys should be valid
        assert len(private_key) == 32
        assert len(public_key) == 32
        assert len(salt) == 64
    
    def test_encrypted_key_roundtrip(self):
        """Encrypted private key should decrypt back to original."""
        password = "my_secure_password"
        
        private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(password)
        
        # encrypted_private_key is: base64encode(fernet.encrypt(private_key))
        # To decrypt: base64decode -> fernet.decrypt
        password_key = EncryptionService.derive_password_key(password, salt)
        fernet = Fernet(password_key)
        
        # Decode the base64 outer layer to get Fernet token
        fernet_token = base64.b64decode(encrypted_private_key)
        
        # Decrypt with Fernet
        decrypted = fernet.decrypt(fernet_token)
        
        assert decrypted == private_key
