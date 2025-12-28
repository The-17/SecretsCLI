import os
import base64
import logging

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# Configure module logger - never logs sensitive data in production
logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Handles all cryptographic operations for SecretsCLI.
    
    Uses Fernet symmetric encryption with PBKDF2-derived keys.
    Master keys are encrypted with user passwords before storage.
    """

    SERVICE_NAME = "secretscli"
    ITERATIONS = 100000  # OWASP recommended minimum for PBKDF2-SHA256

    @staticmethod
    def generate_master_key() -> bytes:
        """Generate a new random master key for encrypting secrets."""
        logger.debug("Generating new master key")
        return Fernet.generate_key()

    @staticmethod
    def generate_salt() -> str:
        """Generate a cryptographically secure random salt (hex-encoded)."""
        logger.debug("Generating new salt")
        return os.urandom(32).hex()

    @staticmethod
    def derive_password_key(password: str, salt_hex: str) -> bytes:
        """
        Derive an encryption key from user password using PBKDF2.
        
        Args:
            password: User's plaintext password
            salt_hex: Hex-encoded salt string
            
        Returns:
            URL-safe base64-encoded derived key suitable for Fernet
        """
        salt = bytes.fromhex(salt_hex)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=EncryptionService.ITERATIONS,
        )
        key = kdf.derive(password.encode())
        logger.debug("Password key derived successfully")
        return base64.urlsafe_b64encode(key)
    
    @staticmethod
    def encrypt_master_key(master_key: bytes, password: str, salt_hex: str) -> str:
        """
        Encrypt the master key with user's password-derived key.
        
        Args:
            master_key: Raw master key bytes
            password: User's plaintext password
            salt_hex: Hex-encoded salt for key derivation
            
        Returns:
            Encrypted master key as a string (safe for storage)
        """
        password_key = EncryptionService.derive_password_key(password, salt_hex)
        cipher = Fernet(password_key)
        encrypted = cipher.encrypt(master_key)
        logger.debug("Master key encrypted successfully")
        return encrypted.decode()

    @staticmethod
    def decrypt_master_key(encrypted_master_key: str, password: str, salt_hex: str) -> bytes:
        """
        Decrypt the master key using user's password.
        
        Args:
            encrypted_master_key: Encrypted master key string
            password: User's plaintext password
            salt_hex: Hex-encoded salt used during encryption
            
        Returns:
            Decrypted master key bytes
            
        Raises:
            cryptography.fernet.InvalidToken: If password is incorrect
        """
        password_key = EncryptionService.derive_password_key(password, salt_hex)
        cipher = Fernet(password_key)
        master_key = cipher.decrypt(encrypted_master_key.encode())
        logger.debug("Master key decrypted successfully")
        return master_key


    @staticmethod
    def setup_user(password):
        master_key = EncryptionService.generate_master_key()
        salt = EncryptionService.generate_salt()

        encrypted_master_key = EncryptionService.encrypt_master_key(master_key, password, salt)
        return master_key, encrypted_master_key, salt
        


