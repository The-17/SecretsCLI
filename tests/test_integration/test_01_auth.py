"""
Integration Tests - Authentication Flow

Tests signup, login, and credential storage against real API.
These run FIRST and establish the test account for subsequent tests.
"""
import pytest
import base64
from typer.testing import CliRunner

from secretscli.cli import app
from secretscli.auth import Auth, _perform_login_
from secretscli.encryption import EncryptionService
from secretscli.utils.credentials import CredentialsManager

from .conftest import TestSession, TEST_EMAIL, TEST_PASSWORD

runner = CliRunner()


@pytest.mark.order(1)
class TestSignup:
    """Test account creation - runs first."""
    
    def test_signup_creates_account(self, test_home):
        """
        Create a fresh test account for this test run.
        
        Uses the unique TEST_EMAIL generated in conftest.py
        """
        # Generate keypair for the test account
        private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(TEST_PASSWORD)
        print(TEST_EMAIL, TEST_PASSWORD)
        # Build signup payload
        user_info = {
            "first_name": "Test",
            "last_name": "User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "public_key": base64.b64encode(public_key).decode(),
            "encrypted_private_key": encrypted_private_key,
            "key_salt": salt
        }
        
        result = Auth.signup(user_info)
        
        assert result is not None, f"Signup failed for {TEST_EMAIL}"
        
        # Store keypair for subsequent tests
        TestSession.private_key = private_key
        TestSession.public_key = public_key


@pytest.mark.order(2)
class TestLogin:
    """Test authentication - runs after signup."""
    
    def test_login_with_created_account(self, test_home):
        """
        Login with the account created in TestSignup.
        """
        credentials = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        # Perform real login
        success = _perform_login_(credentials)
        
        assert success, f"Login failed for {TEST_EMAIL}"
    
    def test_tokens_stored_after_login(self, test_home):
        """After login, tokens should be stored."""
        tokens = CredentialsManager.get_tokens()
        
        assert tokens is not None
        assert tokens.get("access_token") is not None
        assert tokens.get("refresh_token") is not None
    
    def test_email_stored_after_login(self, test_home):
        """After login, email should be stored."""
        email = CredentialsManager.get_email()
        
        assert email == TEST_EMAIL
    
    def test_workspaces_cached_after_login(self, test_home):
        """After login, workspaces should be cached."""
        workspaces = CredentialsManager.get_workspace_keys()
        
        # Should have at least one workspace (personal)
        assert len(workspaces) >= 1
        
        # Store workspace ID for subsequent tests
        for ws_id, ws in workspaces.items():
            if ws.get("type") == "personal":
                TestSession.workspace_id = ws_id
                break
        
        assert TestSession.workspace_id is not None, "No personal workspace found"
    
    def test_private_key_stored_in_keyring(self, test_home):
        """After login, private key should be stored."""
        private_key = CredentialsManager.get_private_key(TEST_EMAIL)
        
        assert private_key is not None
        assert len(private_key) == 32  # X25519 key is 32 bytes
