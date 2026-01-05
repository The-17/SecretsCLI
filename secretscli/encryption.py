"""
Encryption Service

This module handles all cryptographic operations for SecretsCLI.
It implements a zero-knowledge encryption model where the server
never sees plaintext secrets.

SECURITY MODEL:
--------------
1. User creates account with password
2. A random master key is generated (Fernet key)
3. Master key is encrypted using password (PBKDF2 + Fernet)
4. Only the ENCRYPTED master key is stored on the server
5. Secrets are encrypted with the master key before sending to API

This means:
- Server stores only encrypted data
- Without user's password, nothing can be decrypted
- Lost password = lost access (no recovery possible)

ENCRYPTION METHODS:
------------------
- Fernet: Symmetric encryption (AES-128-CBC + HMAC)
- NaCl SealedBox: Asymmetric encryption (X25519 + XSalsa20-Poly1305)
- PBKDF2: Password-based key derivation (100,000 iterations)

KEY CLASSES:
-----------
EncryptionService:
    - setup_user(password) → Generate keypair, encrypt private key
    - generate_keypair() → Create X25519 keypair
    - encrypt_for_user(public_key, data) → Asymmetric encrypt
    - decrypt_from_user(private_key, data) → Asymmetric decrypt
    - encrypt_secret(plain, key) → Encrypt a secret value
    - decrypt_secret(cipher, key) → Decrypt a secret value
    - generate_workspace_key() → Create new workspace encryption key

USAGE:
-----
    from secretscli.encryption import EncryptionService
    
    # Setup user during registration
    private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(password)
    
    # Encrypt a secret with workspace key
    encrypted = EncryptionService.encrypt_secret("sk_live_123")
"""

import base64
import logging
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from nacl.public import PrivateKey, PublicKey, SealedBox

from .utils.credentials import CredentialsManager

# Configure module logger
logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Handles all cryptographic operations for SecretsCLI.
    
    Symmetric: Fernet (AES-128-CBC + HMAC) for secret encryption
    Asymmetric: X25519 + XSalsa20-Poly1305 (NaCl SealedBox) for key wrapping
    Key Derivation: PBKDF2-HMAC-SHA256 for password-based keys
    """

    SERVICE_NAME = "secretscli"
    ITERATIONS = 100000  # OWASP recommended minimum for PBKDF2-SHA256

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
    def setup_user(password: str) -> tuple[bytes, bytes, bytes, str]:
        """
        Setup a new user with keypair for workspace-based encryption.
        
        Generates X25519 keypair, encrypts private key with password-derived key.
        
        Args:
            password: User's plaintext password
            
        Returns:
            Tuple of (private_key, public_key, encrypted_private_key, salt)
            - private_key: 32-byte raw private key
            - public_key: 32-byte raw public key  
            - encrypted_private_key: Base64-encoded Fernet-encrypted private key
            - salt: Hex-encoded PBKDF2 salt
            
        Example:
            private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(password)
        """
        # Generate keypair
        private_key, public_key = EncryptionService.generate_keypair()
        
        # Generate salt and derive user_key from password
        salt = EncryptionService.generate_salt()
        user_key = EncryptionService.derive_password_key(password, salt)
        
        # Encrypt private key with user_key
        cipher = Fernet(user_key)
        encrypted_private_key = base64.b64encode(cipher.encrypt(private_key)).decode()
        
        logger.debug("User keypair generated and encrypted successfully")
        return private_key, public_key, encrypted_private_key, salt

    @staticmethod
    def encrypt_secret(secret: str, workspace_key: bytes = None) -> str:
        """
        Encrypt a secret using the workspace key.
        
        Args:
            secret: Secret string to encrypt
            workspace_key: Optional. If not provided, fetches active workspace key
            
        Returns:
            Encrypted secret as a string (safe for storage)
            
        Example:
            # Auto-fetch workspace key (most common usage)
            encrypted = EncryptionService.encrypt_secret("sk_live_123")
            
            # Explicit workspace key
            encrypted = EncryptionService.encrypt_secret("sk_live_123", workspace_key=key)
        """
        if workspace_key is None:
            workspace_key = CredentialsManager.get_project_workspace_key()
            if workspace_key is None:
                raise ValueError("No workspace key found for this project. Run 'secretscli project use <name>' first.")
        
        cipher = Fernet(workspace_key)
        encrypted = cipher.encrypt(secret.encode())
        logger.debug("Secret encrypted successfully")
        return encrypted.decode()

    @staticmethod
    def decrypt_secret(encrypted_secret: str, workspace_key: bytes = None) -> str:
        """
        Decrypt a secret using the workspace key.
        
        Args:
            encrypted_secret: Encrypted secret string
            workspace_key: Optional. If not provided, fetches from project config
            
        Returns:
            Decrypted secret as a string
            
        Example:
            # Auto-fetch workspace key from project config
            plaintext = EncryptionService.decrypt_secret("gAAAAB...")
            
            # Explicit workspace key
            plaintext = EncryptionService.decrypt_secret("gAAAAB...", workspace_key=key)
        """
        if workspace_key is None:
            workspace_key = CredentialsManager.get_project_workspace_key()
            if workspace_key is None:
                raise ValueError("No workspace key found for this project. Run 'secretscli project use <name>' first.")
        
        cipher = Fernet(workspace_key)
        decrypted = cipher.decrypt(encrypted_secret.encode())
        logger.debug("Secret decrypted successfully")
        return decrypted.decode()

    # ========================
    # ASYMMETRIC ENCRYPTION (NaCl)
    # ========================
    # Used for encrypting workspace keys for team members

    @staticmethod
    def generate_keypair() -> tuple[bytes, bytes]:
        """
        Generate X25519 keypair for asymmetric encryption.
        
        Returns:
            Tuple of (private_key_bytes, public_key_bytes)
            Both are 32 bytes.
            
        Example:
            private_key, public_key = EncryptionService.generate_keypair()
        """
        private_key = PrivateKey.generate()
        public_key = private_key.public_key
        logger.debug("Generated new X25519 keypair")
        return bytes(private_key), bytes(public_key)

    @staticmethod
    def encrypt_for_user(public_key: bytes, data: bytes) -> bytes:
        """
        Encrypt data for a user using their public key (SealedBox).
        
        Used for encrypting workspace keys when inviting team members.
        Only the recipient can decrypt with their private key.
        
        Args:
            public_key: Recipient's 32-byte X25519 public key
            data: Data to encrypt (e.g., workspace key)
            
        Returns:
            Encrypted bytes (includes ephemeral public key + ciphertext)
            
        Example:
            encrypted = EncryptionService.encrypt_for_user(bob_public_key, workspace_key)
        """
        recipient_key = PublicKey(public_key)
        sealed_box = SealedBox(recipient_key)
        encrypted = sealed_box.encrypt(data)
        logger.debug("Encrypted data for user with SealedBox")
        return encrypted

    @staticmethod
    def decrypt_from_user(private_key: bytes, encrypted: bytes) -> bytes:
        """
        Decrypt data that was encrypted with our public key.
        
        Used for decrypting workspace keys received from team invites.
        
        Args:
            private_key: Our 32-byte X25519 private key
            encrypted: Encrypted bytes from encrypt_for_user
            
        Returns:
            Decrypted data bytes
            
        Example:
            workspace_key = EncryptionService.decrypt_from_user(my_private_key, encrypted)
        """
        key = PrivateKey(private_key)
        sealed_box = SealedBox(key)
        decrypted = sealed_box.decrypt(encrypted)
        logger.debug("Decrypted data from SealedBox")
        return decrypted

    @staticmethod
    def generate_workspace_key() -> bytes:
        """
        Generate a new random workspace key for encrypting secrets.
        
        Returns:
            32-byte Fernet-compatible key
            
        Example:
            workspace_key = EncryptionService.generate_workspace_key()
        """
        return Fernet.generate_key()
