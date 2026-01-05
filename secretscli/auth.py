import logging
import base64

from cryptography.fernet import Fernet

from .api.client import api_client
from .encryption import EncryptionService
from .utils.credentials import CredentialsManager

logger = logging.getLogger(__name__)


class Auth:
    """Handles authentication operations with the SecretsCLI API."""

    @staticmethod
    def signup(user_info: dict) -> dict | None:
        """
        Register a new user account.
        
        Args:
            user_info: Dictionary containing:
                - first_name, last_name, email, password
                - public_key (base64): User's X25519 public key
                - encrypted_private_key (base64): Private key encrypted with user_key
                - key_salt (hex): Salt for deriving user_key from password
                       
        Returns:
            API response data on success, None on failure
        """
        response = api_client.call(
            "auth.signup",
            "POST", 
            data={
                "first_name": user_info["first_name"],
                "last_name": user_info["last_name"],
                "email": user_info["email"],
                "password": user_info["password"],
                "public_key": user_info["public_key"],
                "encrypted_private_key": user_info["encrypted_private_key"],
                "key_salt": user_info["key_salt"],
                "terms_agreement": True
            }
        )

        if response.status_code == 201:
            logger.debug("Signup successful")
            return response.json()
        else:
            logger.error("Signup failed: %s", response.json().get("message", "Unknown error"))
            return None

    @staticmethod
    def login(credentials: dict) -> dict | None:
        """
        Authenticate user and obtain tokens.
        
        Args:
            credentials: Dictionary with email and password
            
        Returns:
            API response containing tokens on success, None on failure
        """
        response = api_client.call(
            "auth.login",
            "POST",
            data={
                "email": credentials["email"],
                "password": credentials["password"]
            }
        )

        if response.status_code == 200:
            logger.debug("Login successful")
            return response.json()
        else:
            error_msg = response.json().get("message", "Login failed")
            logger.error("Login failed: %s", error_msg)
            return None


def _perform_login_(credentials: dict, keypair: tuple = None) -> bool:
    """
    Complete login flow: authenticate, decrypt keys, and store credentials.
    
    This helper is used by both init and login commands to avoid code duplication.
    
    Args:
        credentials: Dict with 'email' and 'password'
        keypair: Optional (private_key, public_key) tuple for signup flow.
                 If None, will decrypt from server response.
    
    Returns:
        True on success, False on failure
    """
    
    login_result = Auth.login(credentials)
    
    if login_result is None:
        return False
    
    data = login_result.get("data", {})
    
    # If keypair wasn't provided (login flow), decrypt from server
    if keypair is None:
        encrypted_private_key = data.get("encrypted_private_key")
        salt = data.get("key_salt")
        user_data = data.get("user", {})
        public_key_b64 = user_data.get("public_key")
        
        if not encrypted_private_key or not salt or not public_key_b64:
            logger.error("Login failed: encryption keys not in response")
            return False
        
        try:
            # Derive user_key from password
            user_key = EncryptionService.derive_password_key(credentials["password"], salt)
            
            # Decrypt private key
            cipher = Fernet(user_key)
            private_key = cipher.decrypt(base64.b64decode(encrypted_private_key))
            
            # Get public key from response
            public_key = base64.b64decode(public_key_b64)
        except Exception as e:
            logger.error("Login failed: could not decrypt private key: %s", e)
            return False
    else:
        private_key, public_key = keypair
    
    # Store email and tokens
    CredentialsManager.set_email(credentials["email"])
    CredentialsManager.store_tokens(
        access_token=login_result.get("access_token", data.get("access")),
        refresh_token=login_result.get("refresh_token", data.get("refresh")),
        expires_at=login_result.get("expires_at", data.get("expires_at"))
    )
    
    # Store keypair in keychain
    CredentialsManager.store_keypair(credentials["email"], private_key, public_key)
    
    # Cache all workspace keys globally for fast workspace switching
    workspaces = data.get("workspaces", [])
    workspace_cache = {}
    
    for ws in workspaces:
        try:
            encrypted_ws_key = base64.b64decode(ws["encrypted_workspace_key"])
            workspace_key = EncryptionService.decrypt_from_user(private_key, encrypted_ws_key)
            
            workspace_cache[ws["id"]] = {
                "name": ws["name"],
                "key": base64.b64encode(workspace_key).decode(),
                "role": ws.get("role", "member"),
                "type": ws.get("type", "personal")
            }
        except Exception as e:
            logger.warning("Could not decrypt workspace key for %s: %s", ws.get("name"), e)
    
    if workspace_cache:
        CredentialsManager.store_workspace_keys(workspace_cache)
        
        # Set personal workspace as default for new project creation
        if not CredentialsManager.get_selected_workspace_id():
            # Find personal workspace
            for ws_id, ws in workspace_cache.items():
                if ws.get("type") == "personal":
                    CredentialsManager.set_selected_workspace(ws_id)
                    break
            else:
                # Fallback to first workspace
                first_ws_id = list(workspace_cache.keys())[0]
                CredentialsManager.set_selected_workspace(first_ws_id)
    
    return True
