"""
Tests for EncryptionService

Covers:
- Key generation
- Symmetric encryption (Fernet/workspace keys)
- Asymmetric encryption (X25519/user keys)
- Error cases
"""
import pytest
import base64
from cryptography.fernet import Fernet, InvalidToken
from nacl.public import PrivateKey

from secretscli.encryption import EncryptionService


class TestKeyGeneration:
    """Tests for key generation functions."""
    
    def test_generate_keypair_returns_bytes(self):
        """generate_keypair should return two 32-byte keys."""
        private_key, public_key = EncryptionService.generate_keypair()
        
        assert isinstance(private_key, bytes)
        assert isinstance(public_key, bytes)
        assert len(private_key) == 32
        assert len(public_key) == 32
    
    def test_generate_keypair_unique(self):
        """Each call should generate different keypairs."""
        pair1 = EncryptionService.generate_keypair()
        pair2 = EncryptionService.generate_keypair()
        
        assert pair1[0] != pair2[0]  # Different private keys
        assert pair1[1] != pair2[1]  # Different public keys
    
    def test_generate_workspace_key_valid_fernet(self):
        """generate_workspace_key should return a valid Fernet key."""
        key = EncryptionService.generate_workspace_key()
        
        assert isinstance(key, bytes)
        # Should be usable with Fernet
        fernet = Fernet(key)
        encrypted = fernet.encrypt(b"test")
        assert fernet.decrypt(encrypted) == b"test"


class TestSymmetricEncryption:
    """Tests for workspace key encryption."""
    
    def test_encrypt_decrypt_roundtrip(self, sample_workspace_key):
        """Encrypted value should decrypt back to original."""
        original = "my_secret_api_key_12345"
        
        encrypted = EncryptionService.encrypt_secret(original, sample_workspace_key)
        decrypted = EncryptionService.decrypt_secret(encrypted, sample_workspace_key)
        
        assert decrypted == original
    
    def test_encrypt_returns_string(self, sample_workspace_key):
        """encrypt_secret should return a URL-safe base64-encoded string (Fernet format)."""
        encrypted = EncryptionService.encrypt_secret("test", sample_workspace_key)
        
        assert isinstance(encrypted, str)
        # Fernet uses URL-safe base64, verify it can be decoded
        decoded = base64.urlsafe_b64decode(encrypted)
        assert decoded[0] == 0x80  # Fernet version byte
    
    def test_decrypt_with_wrong_key_fails(self, sample_workspace_key):
        """Decryption with wrong key should raise exception."""
        encrypted = EncryptionService.encrypt_secret("secret", sample_workspace_key)
        wrong_key = Fernet.generate_key()
        
        with pytest.raises(InvalidToken):
            EncryptionService.decrypt_secret(encrypted, wrong_key)
    
    def test_encrypt_empty_string(self, sample_workspace_key):
        """Should handle empty string encryption."""
        encrypted = EncryptionService.encrypt_secret("", sample_workspace_key)
        decrypted = EncryptionService.decrypt_secret(encrypted, sample_workspace_key)
        
        assert decrypted == ""
    
    def test_encrypt_unicode(self, sample_workspace_key):
        """Should handle unicode characters."""
        original = "密码🔐パスワード"
        
        encrypted = EncryptionService.encrypt_secret(original, sample_workspace_key)
        decrypted = EncryptionService.decrypt_secret(encrypted, sample_workspace_key)
        
        assert decrypted == original


class TestAsymmetricEncryption:
    """Tests for user key encryption (X25519 + SealedBox)."""
    
    def test_encrypt_for_user_roundtrip(self, sample_keypair):
        """encrypt_for_user/decrypt_from_user should roundtrip."""
        private_key, public_key = sample_keypair
        original = b"workspace_key_bytes_here"
        
        encrypted = EncryptionService.encrypt_for_user(public_key, original)
        decrypted = EncryptionService.decrypt_from_user(private_key, encrypted)
        
        assert decrypted == original
    
    def test_encrypt_for_user_different_each_time(self, sample_keypair):
        """Same plaintext should produce different ciphertext (randomized)."""
        private_key, public_key = sample_keypair
        plaintext = b"same_data"
        
        encrypted1 = EncryptionService.encrypt_for_user(public_key, plaintext)
        encrypted2 = EncryptionService.encrypt_for_user(public_key, plaintext)
        
        # Ciphertext should differ due to nonce randomization
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same value
        assert EncryptionService.decrypt_from_user(private_key, encrypted1) == plaintext
        assert EncryptionService.decrypt_from_user(private_key, encrypted2) == plaintext
    
    def test_decrypt_with_wrong_key_fails(self, sample_keypair):
        """Decryption with wrong private key should fail."""
        _, public_key = sample_keypair
        wrong_private = bytes(PrivateKey.generate())
        
        encrypted = EncryptionService.encrypt_for_user(public_key, b"secret")
        
        with pytest.raises(Exception):  # nacl CryptoError
            EncryptionService.decrypt_from_user(wrong_private, encrypted)


class TestSetupUser:
    """Tests for setup_user helper function."""
    
    def test_setup_user_returns_valid_data(self):
        """setup_user should return valid keypair and encrypted private key."""
        password = "test_password_123"
        private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(password)
        
        assert isinstance(private_key, bytes)
        assert isinstance(public_key, bytes)
        assert len(private_key) == 32
        assert len(public_key) == 32
        # encrypted_private_key is base64-encoded string (wraps Fernet token)
        assert isinstance(encrypted_private_key, str)
        assert isinstance(salt, str)
        assert len(salt) == 64  # 32 bytes as hex = 64 chars
    
    def test_setup_user_encrypted_key_is_decryptable(self):
        """Encrypted private key should be decryptable with correct password."""
        password = "my_secure_password"
        
        private_key, public_key, encrypted_private_key, salt = EncryptionService.setup_user(password)
        
        # encrypted_private_key is base64.b64encode(fernet.encrypt(private_key)).decode()
        # So we need to: decode string -> base64 decode -> fernet decrypt
        password_key = EncryptionService.derive_password_key(password, salt)
        fernet = Fernet(password_key)
        
        # First decode the outer base64 layer
        fernet_token = base64.b64decode(encrypted_private_key)
        
        # Then decrypt with Fernet
        decrypted_private_key = fernet.decrypt(fernet_token)
        
        assert decrypted_private_key == private_key
