"""
Credentials Manager for SecretsCLI

Handles all credential storage operations:
- JWT tokens (access/refresh) → stored in ~/.secretscli/token.json
- User email → stored in ~/.secretscli/config.json  
- Private key → stored in OS keychain (via keyring)
- Workspace keys → cached in ~/.secretscli/config.json (keyed by workspace_id)
- Project config → stored in ./.secretscli/project.json

Usage:
    from secretscli.utils.credentials import CredentialsManager
    
    # After login
    CredentialsManager.store_tokens(access, refresh, expires)
    CredentialsManager.set_email(email)
    CredentialsManager.store_keypair(email, private_key, public_key)
    
    # For API calls
    token = CredentialsManager.get_access_token()
    
    # For decrypting secrets
    workspace_key = CredentialsManager.get_project_workspace_key()
"""

import json
import sys, base64
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
        
        The email is used as the keyring identifier for the private key.
        
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

    # Project Config Management (file-based: ./.secretscli/project.json)

    @staticmethod
    def config_project(
        project_id: str, 
        project_name: str, 
        description: str = None, 
        environment: str = "development",
        workspace_id: str = None,
        workspace_name: str = None,
        last_pull: str = None, 
        last_push: str = None
    ) -> bool | None:
        """
        Configure the current directory's project binding.
        
        Note: workspace_key is NOT stored in project.json for security.
        It's retrieved from global config via workspace_id.
        
        Args:
            project_id: UUID of the project
            project_name: Human-readable project name
            description: Optional project description
            environment: One of "development", "staging", "production"
            workspace_id: UUID of the workspace this project belongs to
            workspace_name: Workspace display name
            last_pull: ISO timestamp of last pull (optional)
            last_push: ISO timestamp of last push (optional)
            
        Returns:
            True on success, None if project.json doesn't exist
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
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "last_pull": last_pull,
            "last_push": last_push
        }

        project_file.write_text(json.dumps(configs, indent=2))
        return True

    @staticmethod
    def update_project_config(**kwargs) -> bool:
        """
        Update specific fields in project config without overwriting others.
        
        Args:
            **kwargs: Fields to update (e.g., last_pull="2024-01-01T...")
            
        Returns:
            True on success, False if not in a project directory
        """
        config = CredentialsManager.get_project_config()
        if not config:
            return False
        
        config.update(kwargs)
        
        project_file = Path.cwd() / ".secretscli" / "project.json"
        project_file.write_text(json.dumps(config, indent=2))
        return True

    @staticmethod
    def get_project_config() -> dict | None:
        """Get the full project configuration for current directory."""
        project_config_dir = Path.cwd() / ".secretscli"
        project_file = project_config_dir / "project.json"

        if not project_file.exists():
            return None
        
        return json.loads(project_file.read_text())

    @staticmethod
    def get_project_id() -> str | None:
        """Get just the project ID for the current directory."""
        config = CredentialsManager.get_project_config()
        return config.get("project_id") if config else None

    @staticmethod
    def get_project_name() -> str | None:
        """Get the project name for the current directory."""
        config = CredentialsManager.get_project_config()
        return config.get("project_name") if config else None

    @staticmethod
    def get_project_workspace_key() -> bytes | None:
        """
        Get the workspace key for the current project directory.
        
        Retrieves the workspace_id from project.json and looks up the
        corresponding key from the global workspace cache.
        
        Returns:
            Workspace key bytes, or None if not found
        """
        workspace_id = CredentialsManager.get_project_workspace_id()
        if not workspace_id:
            return None
        return CredentialsManager.get_workspace_key(workspace_id)

    @staticmethod
    def get_project_workspace_id() -> str | None:
        """Get the workspace ID for the current project directory."""
        config = CredentialsManager.get_project_config()
        return config.get("workspace_id") if config else None

    # Session Management

    @staticmethod
    def clear_session() -> bool:
        """
        Logout: clear all stored credentials.
        
        Removes:
        - Private key from OS keychain
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
            True if both access token and private key are available
            
        Note:
            This doesn't validate token expiry - just checks presence.
            For full validation, also check expires_at from get_tokens().
        """
        email = CredentialsManager.get_email()
        return (
            CredentialsManager.get_access_token() is not None
            and CredentialsManager.get_private_key(email) is not None
        )

    # KEY PAIR MANAGEMENT (OS Keychain)

    @staticmethod
    def store_keypair(email: str, private_key: bytes, public_key: bytes) -> bool:
        """
        Store user's keypair in OS keychain.
        
        Args:
            email: User's email (used as keychain identifier)
            private_key: 32-byte X25519 private key
            public_key: 32-byte X25519 public key
            
        Returns:
            True on success
        """
        keyring.set_password(KEYRING_SERVICE, f"{email}_private_key", base64.b64encode(private_key).decode())
        keyring.set_password(KEYRING_SERVICE, f"{email}_public_key", base64.b64encode(public_key).decode())
        return True

    @staticmethod
    def store_private_key(email: str, private_key: bytes) -> bool:
        """Store user's private key in OS keychain (legacy, prefer store_keypair)."""
        encoded = base64.b64encode(private_key).decode()
        keyring.set_password(KEYRING_SERVICE, f"{email}_private_key", encoded)
        return True

    @staticmethod
    def get_private_key(email: str = None) -> bytes | None:
        """Retrieve user's private key from OS keychain."""
        email = email or CredentialsManager.get_email()
        if not email:
            return None
        encoded = keyring.get_password(KEYRING_SERVICE, f"{email}_private_key")
        return base64.b64decode(encoded) if encoded else None

    @staticmethod
    def get_public_key(email: str = None) -> bytes | None:
        """Retrieve user's public key from OS keychain."""
        email = email or CredentialsManager.get_email()
        if not email:
            return None
        encoded = keyring.get_password(KEYRING_SERVICE, f"{email}_public_key")
        return base64.b64decode(encoded) if encoded else None

    # ========================
    # GLOBAL WORKSPACE CACHE (for fast workspace switching)
    # ========================

    @staticmethod
    def store_workspace_keys(workspaces: dict) -> bool:
        """
        Store decrypted workspace keys to global config (cache).
        
        Args:
            workspaces: Dict of workspace_id -> {name, key (base64), role}
        """
        config = CredentialsManager._load_global_config()
        config["workspaces"] = workspaces
        global_config_file.write_text(json.dumps(config, indent=2))
        return True

    @staticmethod
    def get_workspace_keys() -> dict:
        """Get all cached workspace keys."""
        config = CredentialsManager._load_global_config()
        return config.get("workspaces", {})

    @staticmethod
    def get_workspace_key(workspace_id: str) -> bytes | None:
        """Get workspace key from global cache by ID."""
        workspaces = CredentialsManager.get_workspace_keys()
        ws = workspaces.get(workspace_id)
        if ws and ws.get("key"):
            return base64.b64decode(ws["key"])
        return None

    @staticmethod
    def get_workspace(workspace_id: str) -> dict:
        """Get workspace info from global cache. Returns empty dict if not found."""
        workspaces = CredentialsManager.get_workspace_keys()
        return workspaces.get(workspace_id, {})

    @staticmethod
    def get_selected_workspace_id() -> str | None:
        """
        Get the selected workspace for NEW project creation.
        This is NOT the workspace of the current project - use get_project_workspace_id() for that.
        """
        config = CredentialsManager._load_global_config()
        return config.get("selected_workspace_id")

    @staticmethod
    def set_selected_workspace(workspace_id: str) -> bool:
        """
        Set the selected workspace for NEW project creation.
        Does NOT affect existing projects' workspace binding.
        """
        config = CredentialsManager._load_global_config()
        config["selected_workspace_id"] = workspace_id
        global_config_file.write_text(json.dumps(config, indent=2))
        return True

    @staticmethod
    def _load_global_config() -> dict:
        """Load global config file, return empty dict if not found."""
        if not global_config_file.exists():
            return {}
        try:
            return json.loads(global_config_file.read_text())
        except json.JSONDecodeError:
            return {}