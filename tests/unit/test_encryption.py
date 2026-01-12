"""Tests for token encryption utilities."""

from __future__ import annotations

import pytest

from gmail_multi_user.exceptions import TokenError
from gmail_multi_user.tokens.encryption import TokenEncryption


class TestTokenEncryption:
    """Tests for TokenEncryption class."""

    def test_generate_key_returns_valid_key(self) -> None:
        """Test that generate_key returns a valid Fernet key."""
        key = TokenEncryption.generate_key()

        # Should be 44 characters (base64-encoded 32 bytes)
        assert len(key) == 44
        assert key.endswith("=")

        # Should be usable
        encryptor = TokenEncryption(key)
        assert encryptor.validate_key()

    def test_generate_key_hex_returns_valid_key(self) -> None:
        """Test that generate_key_hex returns a valid hex key."""
        key = TokenEncryption.generate_key_hex()

        # Should be 64 characters (hex-encoded 32 bytes)
        assert len(key) == 64

        # Should be usable
        encryptor = TokenEncryption(key)
        assert encryptor.validate_key()

    def test_encrypt_decrypt_round_trip(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that encrypt/decrypt returns original value."""
        original = "my-secret-token-12345"

        encrypted = token_encryptor.encrypt(original)
        decrypted = token_encryptor.decrypt(encrypted)

        assert decrypted == original
        assert encrypted != original  # Should actually be encrypted

    def test_encrypt_produces_different_ciphertext(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that encrypting same value twice produces different ciphertext."""
        original = "my-secret-token"

        encrypted1 = token_encryptor.encrypt(original)
        encrypted2 = token_encryptor.encrypt(original)

        # Fernet includes random IV, so each encryption is different
        assert encrypted1 != encrypted2

        # But both should decrypt to the same value
        assert token_encryptor.decrypt(encrypted1) == original
        assert token_encryptor.decrypt(encrypted2) == original

    def test_encrypt_handles_unicode(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that encryption handles Unicode strings."""
        original = "token-with-unicode-\u2603-\u2764-emoji"

        encrypted = token_encryptor.encrypt(original)
        decrypted = token_encryptor.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_handles_empty_string(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that encryption handles empty strings."""
        original = ""

        encrypted = token_encryptor.encrypt(original)
        decrypted = token_encryptor.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_handles_long_string(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that encryption handles long strings."""
        original = "x" * 10000

        encrypted = token_encryptor.encrypt(original)
        decrypted = token_encryptor.decrypt(encrypted)

        assert decrypted == original

    def test_decrypt_with_wrong_key_raises_error(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that decrypting with wrong key raises TokenError."""
        original = "my-secret-token"
        encrypted = token_encryptor.encrypt(original)

        # Create new encryptor with different key
        other_key = TokenEncryption.generate_key()
        other_encryptor = TokenEncryption(other_key)

        with pytest.raises(TokenError) as exc_info:
            other_encryptor.decrypt(encrypted)

        assert exc_info.value.code == "encryption_error"

    def test_decrypt_tampered_ciphertext_raises_error(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that decrypting tampered ciphertext raises TokenError."""
        original = "my-secret-token"
        encrypted = token_encryptor.encrypt(original)

        # Tamper with the ciphertext
        tampered = encrypted[:-5] + "XXXXX"

        with pytest.raises(TokenError) as exc_info:
            token_encryptor.decrypt(tampered)

        assert exc_info.value.code == "encryption_error"

    def test_invalid_key_raises_error(self) -> None:
        """Test that invalid key raises TokenError."""
        with pytest.raises(TokenError) as exc_info:
            TokenEncryption("invalid-key")

        assert exc_info.value.code == "encryption_error"

    def test_key_too_short_raises_error(self) -> None:
        """Test that short key raises TokenError."""
        with pytest.raises(TokenError) as exc_info:
            TokenEncryption("abc123")

        assert exc_info.value.code == "encryption_error"

    def test_accepts_base64_key(self, encryption_key: str) -> None:
        """Test that base64-encoded key is accepted."""
        encryptor = TokenEncryption(encryption_key)
        assert encryptor.validate_key()

    def test_accepts_hex_key(self, encryption_key_hex: str) -> None:
        """Test that hex-encoded key is accepted."""
        encryptor = TokenEncryption(encryption_key_hex)
        assert encryptor.validate_key()

    def test_validate_key_returns_true_for_valid(
        self,
        token_encryptor: TokenEncryption,
    ) -> None:
        """Test that validate_key returns True for valid configuration."""
        assert token_encryptor.validate_key() is True

    def test_keys_are_interchangeable(self) -> None:
        """Test that base64 and hex keys derived from same bytes work together."""
        import base64

        # Generate raw key bytes
        import secrets

        key_bytes = secrets.token_bytes(32)

        # Create base64 and hex versions
        base64_key = base64.urlsafe_b64encode(key_bytes).decode()
        hex_key = key_bytes.hex()

        # Both should work and produce same decryption
        encryptor1 = TokenEncryption(base64_key)
        encryptor2 = TokenEncryption(hex_key)

        original = "test-data"
        encrypted = encryptor1.encrypt(original)

        # Both should be able to decrypt
        assert encryptor1.decrypt(encrypted) == original
        assert encryptor2.decrypt(encrypted) == original
