"""
Credentials Manager for SecretsCLI

Handles all credential storage operations:
- JWT tokens (access/refresh) → stored in ~/.secretscli/token.json
- User email → stored in ~/.secretscli/config.json  
- Master encryption key → stored in OS keychain (via keyring)
- Project config → stored in ./.secretscli/project.json

Usage:
    from secretscli.utils.credentials import CredentialsManager
    
    # After login
    CredentialsManager.store_tokens(access, refresh, expires)
    CredentialsManager.set_email(email)
    CredentialsManager.store_master_key(email, master_key)
    
    # For API calls
    token = CredentialsManager.get_access_token()
    
    # For decrypting secrets
    key = CredentialsManager.get_master_key(email)
"""

import json
import sys
from pathlib import Path

import keyring
from keyring.errors import PasswordDeleteError

from ..config import global_config_file, token_file, CONFIG_SCHEMA, TOKEN_SCHEMA, global_config_dir


KEYRING_SERVICE = "SecretsCLI"


def _configure_keyring():
    """
    Configure keyring backend based on platform.
    
    Uses the best available backend:
    - macOS: macOS Keychain (default)
    - Windows: Windows Credential Manager (default)  
    - Linux: Secret Service if available, otherwise PlaintextKeyring
    """
    # First, try to use the default backend
    try:
        # Test if the default backend works
        keyring.get_keyring()
        test_result = keyring.get_password("__secretscli_test__", "__test__")
        # If we get here without exception, the default backend works
        return
    except Exception:
        pass
    
    # Fallback: use keyrings.alt PlaintextKeyring
    # This works everywhere but stores passwords in plaintext
    # We mitigate this by storing in our own protected config directory
    try:
        from keyrings.alt.file import PlaintextKeyring
        
        # Configure PlaintextKeyring to use our config directory
        kr = PlaintextKeyring()
        kr.file_path = str(global_config_dir / "keyring.cfg")
        keyring.set_keyring(kr)
    except ImportError:
        # keyrings.alt not installed - user needs to install it
        pass


# Configure keyring on module import
_configure_keyring()


class CredentialsManager:
    """
    Centralized credential storage manager.
    
    All methods are static - no instantiation needed.
    """

    # Token Management (file-based: ~/.secretscli/token.json)

    @staticmethod
    def store_tokens(access_token: str, refresh_token: str, expires_at: str) -> bool:
        """
        Store authentication tokens after login.
        
        Args:
            access_token: JWT access token for API authorization
            refresh_token: JWT refresh token for obtaining new access tokens
            expires_at: ISO timestamp when access_token expires
            
        Returns:
            True on success
            
        Example:
            CredentialsManager.store_tokens(
                "eyJ...", 
                "eyJ...", 
                "2024-01-01T12:00:00Z"
            )
        """
        tokens = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at
        }
        token_file.write_text(json.dumps(tokens, indent=2))
        return True

    @staticmethod
    def get_tokens() -> dict | None:
        """
        Load all tokens from storage.
        
        Returns:
            Dict with access_token, refresh_token, expires_at keys,
            or None if token file doesn't exist
        """
        if not token_file.exists():
            return None
        return json.loads(token_file.read_text())

    @staticmethod
    def get_access_token() -> str | None:
        """
        Get the current access token for API calls.
        
        Returns:
            Access token string, or None if not logged in
            
        Example:
            token = CredentialsManager.get_access_token()
            headers = {"Authorization": f"Bearer {token}"}
        """
        tokens = CredentialsManager.get_tokens()
        return tokens.get("access_token") if tokens else None

    @staticmethod
    def store_access_token(access_token: str) -> bool:
        """
        Update only the access token (used after refresh).
        
        Args:
            access_token: New JWT access token
            
        Returns:
            True on success, False if no existing tokens to update
        """
        tokens = CredentialsManager.get_tokens()
        if tokens is None:
            return False
        
        tokens["access_token"] = access_token
        CredentialsManager.store_tokens(**tokens)
        return True

    # Email/Config Management (file-based: ~/.secretscli/config.json)

    @staticmethod
    def set_email(email: str) -> bool:
        """
        Store the user's email address.
        
        The email is used as the keyring identifier for the master key.
        
        Args:
            email: User's email address
            
        Returns:
            True on success
        """
        global_config_file.write_text(json.dumps({"email": email}, indent=2))
        return True

    @staticmethod
    def get_email() -> str | None:
        """
        Get the stored user email.
        
        Returns:
            Email string, or None if not logged in
        """
        if not global_config_file.exists():
            return None
        config = json.loads(global_config_file.read_text())
        return config.get("email")

    # Master Key Management (OS keychain via keyring)

    @staticmethod
    def store_master_key(email: str, master_key: bytes) -> bool:
        """
        Store the decrypted master key in OS keychain.
        
        The master key is used to encrypt/decrypt secrets. It's stored
        in the OS keychain (macOS Keychain, Windows Credential Manager,
        or Linux Secret Service) for security.
        
        Args:
            email: User's email (used as keychain identifier)
            master_key: Decrypted master key bytes
            
        Returns:
            True on success
            
        Note:
            Call this immediately after login while you still have
            the user's password to decrypt the master key.
        """
        keyring.set_password(KEYRING_SERVICE, email, master_key.decode())
        return True

    @staticmethod
    def get_master_key(email: str = None) -> bytes | None:
        """
        Retrieve the master key from OS keychain.
        
        Args:
            email: User's email (optional, will use stored email if not provided)
            
        Returns:
            Master key bytes, or None if not found
            
        Example:
            key = CredentialsManager.get_master_key()
            decrypted = Fernet(key).decrypt(encrypted_secret)
        """
        email = email or CredentialsManager.get_email()
        if not email:
            return None
        key = keyring.get_password(KEYRING_SERVICE, email)
        return key.encode() if key else None

    # Project Config Management (file-based: ./.secretscli/project.json)

    @staticmethod
    def config_project(project_id: str, project_name: str, description: str = None, environment: str = "development", last_pull: str = None, last_push: str = None) -> bool | None:
        """
        Configure the current directory's project binding.
        
        Links the current working directory to a SecretsCLI project.
        
        Args:
            project_id: UUID of the project
            project_name: Human-readable project name
            description: Optional project description
            environment: One of "development", "staging", "production"
            last_pull: ISO timestamp of last pull (optional)
            last_push: ISO timestamp of last push (optional)
            
        Returns:
            True on success, None if project.json doesn't exist
            
        Example:
            CredentialsManager.config_project(
                "123e4567-e89b-12d3-a456-426614174000",
                "my-web-app",
                "My awesome project",
                "production"
            )
        """
        project_config_dir = Path.cwd() / ".secretscli"
        project_file = project_config_dir / "project.json"

        if not project_file.exists():
            return None
        
        configs = {
            "project_id": project_id,
            "project_name": project_name,
            "description": description,
            "environment": environment,
            "last_pull": last_pull,
            "last_push": last_push
        }

        project_file.write_text(json.dumps(configs, indent=2))
        return True

    @staticmethod
    def get_project_config() -> dict | None:
        """
        Get the full project configuration for current directory.
        
        Returns:
            Dict with project_id, project_name, environment, last_pull, last_push,
            or None if not in a SecretsCLI project directory
        """
        project_config_dir = Path.cwd() / ".secretscli"
        project_file = project_config_dir / "project.json"

        if not project_file.exists():
            return None
        
        return json.loads(project_file.read_text())

    @staticmethod
    def get_project_id() -> str | None:
        """
        Get just the project ID for the current directory.
        
        Returns:
            Project UUID string, or None if not in a project directory
        """
        config = CredentialsManager.get_project_config()
        return config.get("project_id") if config else None

    # Session Management

    @staticmethod
    def clear_session() -> bool:
        """
        Logout: clear all stored credentials.
        
        Removes:
        - Master key from OS keychain
        - Tokens from token.json
        - Email from config.json
        
        Returns:
            True on success
            
        Note:
            This does NOT clear project.json (project binding persists).
        """
        email = CredentialsManager.get_email()
        
        # Clear keyring if we have an email
        if email:
            try:
                keyring.delete_password(KEYRING_SERVICE, email)
            except PasswordDeleteError:
                pass  # Already deleted or never existed

        # Always reset files to defaults
        global_config_file.write_text(json.dumps(CONFIG_SCHEMA, indent=2))
        token_file.write_text(json.dumps(TOKEN_SCHEMA, indent=2))
        
        return True

    @staticmethod
    def is_authenticated() -> bool:
        """
        Check if user has a valid session.
        
        Returns:
            True if both access token and master key are available
            
        Note:
            This doesn't validate token expiry - just checks presence.
            For full validation, also check expires_at from get_tokens().
        """
        email = CredentialsManager.get_email()
        return (
            CredentialsManager.get_access_token() is not None
            and CredentialsManager.get_master_key(email) is not None
        )