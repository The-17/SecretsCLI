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
