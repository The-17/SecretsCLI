import logging

from .api.client import api_client

logger = logging.getLogger(__name__)


class Auth:
    """Handles authentication operations with the SecretsCLI API."""

    @staticmethod
    def signup(user_info: dict) -> dict | None:
        """
        Register a new user account.
        
        Args:
            user_info: Dictionary containing first_name, last_name, email, 
                       password, encrypted_master_key, and key_salt
                       
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
                "encrypted_master_key": user_info["encrypted_master_key"],
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


def _perform_login_(credentials: dict, master_key: bytes = None) -> bool:
    """
    Complete login flow: authenticate, decrypt master key, and store credentials.
    
    This helper is used by both init and login commands to avoid code duplication.
    
    Args:
        credentials: Dict with 'email' and 'password'
        master_key: Pre-generated master key (for signup flow). 
                    If None, will decrypt from server response.
    
    Returns:
        True on success, False on failure
    """
    from .encryption import EncryptionService
    from .utils.credentials import CredentialsManager
    
    login_result = Auth.login(credentials)
    
    if login_result is None:
        return False
    
    data = login_result.get("data", {})
    
    # If master_key wasn't provided (login flow), decrypt it from server
    if master_key is None:
        encrypted_master_key = data.get("encrypted_master_key")
        salt = data.get("key_salt")
        
        if not encrypted_master_key or not salt:
            logger.error("Login failed: encryption keys not in response")
            return False
        
        try:
            master_key = EncryptionService.decrypt_master_key(
                encrypted_master_key, 
                credentials["password"], 
                salt
            )
        except Exception as e:
            logger.error("Login failed: could not decrypt master key: %s", e)
            return False
    
    # Store all credentials
    CredentialsManager.set_email(credentials["email"])
    CredentialsManager.store_master_key(credentials["email"], master_key)
    CredentialsManager.store_tokens(
        access_token=login_result.get("access_token", data.get("access")),
        refresh_token=login_result.get("refresh_token", data.get("refresh")),
        expires_at=login_result.get("expires_at", "")
    )
    
    return True
