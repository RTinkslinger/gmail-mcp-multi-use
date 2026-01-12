"""Token encryption utilities using Fernet.

This module provides symmetric encryption for OAuth tokens using
Fernet (AES-128-CBC + HMAC-SHA256).
"""

from __future__ import annotations

import base64
import secrets

from cryptography.fernet import Fernet, InvalidToken

from gmail_multi_user.exceptions import TokenError


class TokenEncryption:
    """Encrypt and decrypt OAuth tokens using Fernet.

    Fernet provides symmetric encryption using AES-128-CBC with HMAC-SHA256
    for authentication. Keys are 32 bytes (256 bits).

    Example:
        # Generate a new key
        key = TokenEncryption.generate_key()

        # Create encryptor
        encryptor = TokenEncryption(key)

        # Encrypt and decrypt
        encrypted = encryptor.encrypt("my-secret-token")
        decrypted = encryptor.decrypt(encrypted)
    """

    def __init__(self, key: str) -> None:
        """Initialize the encryptor with a key.

        Args:
            key: Fernet key as base64 (44 chars) or hex (64 chars).

        Raises:
            TokenError: If the key is invalid.
        """
        self._key = self._normalize_key(key)
        try:
            self._fernet = Fernet(self._key)
        except Exception as e:
            raise TokenError(
                message=f"Invalid encryption key: {e}",
                code="encryption_error",
            ) from e

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded ciphertext.

        Raises:
            TokenError: If encryption fails.
        """
        try:
            ciphertext = self._fernet.encrypt(plaintext.encode("utf-8"))
            return ciphertext.decode("utf-8")
        except Exception as e:
            raise TokenError(
                message=f"Encryption failed: {e}",
                code="encryption_error",
            ) from e

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string.

        Args:
            ciphertext: Base64-encoded ciphertext from encrypt().

        Returns:
            The original plaintext string.

        Raises:
            TokenError: If decryption fails (invalid key or tampered data).
        """
        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as e:
            raise TokenError(
                message="Decryption failed: invalid key or tampered data",
                code="encryption_error",
            ) from e
        except Exception as e:
            raise TokenError(
                message=f"Decryption failed: {e}",
                code="encryption_error",
            ) from e

    def validate_key(self) -> bool:
        """Validate that the key is working correctly.

        Returns:
            True if the key can encrypt and decrypt successfully.
        """
        try:
            test_data = "test_encryption_validation"
            encrypted = self.encrypt(test_data)
            decrypted = self.decrypt(encrypted)
            return decrypted == test_data
        except TokenError:
            return False

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet-compatible encryption key.

        Returns:
            A new 32-byte key encoded as URL-safe base64.
        """
        return Fernet.generate_key().decode("utf-8")

    @staticmethod
    def generate_key_hex() -> str:
        """Generate a new encryption key as hex string.

        Returns:
            A new 32-byte key encoded as hexadecimal.
        """
        return secrets.token_hex(32)

    @staticmethod
    def _normalize_key(key: str) -> bytes:
        """Normalize key to Fernet format (base64 bytes).

        Args:
            key: Key as base64 (44 chars) or hex (64 chars).

        Returns:
            Key as base64-encoded bytes.

        Raises:
            TokenError: If the key format is invalid.
        """
        key = key.strip()

        # Check if it's already valid base64 Fernet key (44 chars with = padding)
        if len(key) == 44 and key.endswith("="):
            try:
                # Validate it's proper base64
                decoded = base64.urlsafe_b64decode(key)
                if len(decoded) == 32:
                    return key.encode("utf-8")
            except Exception:
                pass

        # Check if it's hex-encoded (64 chars)
        if len(key) == 64:
            try:
                key_bytes = bytes.fromhex(key)
                if len(key_bytes) == 32:
                    # Convert to base64 for Fernet
                    return base64.urlsafe_b64encode(key_bytes)
            except ValueError:
                pass

        raise TokenError(
            message=(
                "Invalid encryption key format. "
                "Key must be 44-character base64 (ending with =) "
                "or 64-character hex string."
            ),
            code="encryption_error",
        )
