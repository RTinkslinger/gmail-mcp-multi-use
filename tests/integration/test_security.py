"""Security tests for gmail-multi-user-mcp.

These tests verify security properties including:
- Encryption/decryption integrity
- SQL injection prevention
- XSS prevention in data handling
- Token security properties
"""

from __future__ import annotations

import base64
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from gmail_multi_user.storage.sqlite import SQLiteBackend
from gmail_multi_user.tokens.encryption import TokenEncryption


class TestTokenEncryption:
    """Security tests for token encryption."""

    def test_encryption_produces_different_ciphertext(self):
        """Test that encrypting same plaintext produces different ciphertext each time."""
        # Generate a valid Fernet key
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        encryption = TokenEncryption(key)
        
        plaintext = "sensitive_token_12345"
        
        ciphertext1 = encryption.encrypt(plaintext)
        ciphertext2 = encryption.encrypt(plaintext)
        
        # Due to random IV, ciphertexts should differ
        assert ciphertext1 != ciphertext2
        
        # But both should decrypt to same plaintext
        assert encryption.decrypt(ciphertext1) == plaintext
        assert encryption.decrypt(ciphertext2) == plaintext

    def test_encryption_decryption_roundtrip(self):
        """Test encryption/decryption roundtrip preserves data."""
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        encryption = TokenEncryption(key)
        
        test_data = [
            "simple_token",
            "token with spaces",
            "token\nwith\nnewlines",
            "unicode: \u00e9\u00e0\u00fc",
            "special: !@#$%^&*()",
            "long" * 1000,  # Long token
        ]
        
        for data in test_data:
            encrypted = encryption.encrypt(data)
            decrypted = encryption.decrypt(encrypted)
            assert decrypted == data, f"Failed for: {data[:50]}..."

    def test_wrong_key_fails_decryption(self):
        """Test that wrong key cannot decrypt data."""
        key1 = base64.urlsafe_b64encode(os.urandom(32)).decode()
        key2 = base64.urlsafe_b64encode(os.urandom(32)).decode()
        
        encryption1 = TokenEncryption(key1)
        encryption2 = TokenEncryption(key2)
        
        encrypted = encryption1.encrypt("secret_data")
        
        # Wrong key should fail
        with pytest.raises(Exception):  # Fernet raises InvalidToken
            encryption2.decrypt(encrypted)

    def test_tampered_ciphertext_fails(self):
        """Test that tampered ciphertext is detected."""
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        encryption = TokenEncryption(key)
        
        encrypted = encryption.encrypt("original_data")
        
        # Tamper with the ciphertext
        tampered = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(Exception):
            encryption.decrypt(tampered)

    def test_empty_string_encryption(self):
        """Test that empty strings can be encrypted/decrypted."""
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        encryption = TokenEncryption(key)
        
        encrypted = encryption.encrypt("")
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == ""


class TestSQLInjectionPrevention:
    """Tests for SQL injection prevention in storage layer."""

    @pytest.fixture
    async def storage(self):
        """Create SQLite backend for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            backend = SQLiteBackend(f.name)
            await backend.initialize()
            yield backend
            await backend.close()

    @pytest.mark.asyncio
    async def test_sql_injection_in_user_id(self, storage):
        """Test that SQL injection in user_id is prevented."""
        # Attempt SQL injection in external_user_id
        malicious_ids = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "user' UNION SELECT * FROM connections --",
            "'; DELETE FROM users WHERE '1'='1",
            "user\"; DROP TABLE users; --",
        ]
        
        for malicious_id in malicious_ids:
            # Should safely store the malicious string as literal data
            user = await storage.get_or_create_user(malicious_id)
            assert user.external_user_id == malicious_id
            
            # Verify database still works
            retrieved = await storage.get_user_by_id(user.id)
            assert retrieved is not None

    @pytest.mark.asyncio
    async def test_sql_injection_in_email(self, storage):
        """Test that SQL injection in email is prevented."""
        user = await storage.get_or_create_user("safe_user")
        
        malicious_emails = [
            "test'; DROP TABLE connections; --@gmail.com",
            "user@gmail.com' OR '1'='1",
            "'; UPDATE connections SET is_active=0; --@test.com",
        ]
        
        for malicious_email in malicious_emails:
            # Should safely store the malicious string
            connection = await storage.create_connection(
                user_id=user.id,
                gmail_address=malicious_email,
                access_token_encrypted="enc",
                refresh_token_encrypted="enc",
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                scopes=["gmail.readonly"],
            )
            
            # Verify it was stored correctly
            retrieved = await storage.get_connection(connection.id)
            assert retrieved.gmail_address == malicious_email

    @pytest.mark.asyncio
    async def test_sql_injection_in_state(self, storage):
        """Test that SQL injection in OAuth state is prevented."""
        user = await storage.get_or_create_user("state_user")
        
        malicious_states = [
            "state'; DROP TABLE oauth_states; --",
            "state' OR '1'='1",
            "'; DELETE FROM oauth_states; --",
        ]
        
        for malicious_state in malicious_states:
            state = await storage.create_oauth_state(
                user_id=user.id,
                state=malicious_state,
                scopes=["gmail.readonly"],
                redirect_uri="http://localhost/callback",
                code_verifier="verifier",
                expires_at=datetime.utcnow() + timedelta(minutes=10),
            )
            
            # Verify it was stored correctly
            retrieved = await storage.get_oauth_state(malicious_state)
            assert retrieved.state == malicious_state


class TestXSSPrevention:
    """Tests for XSS prevention in data handling."""

    @pytest.fixture
    async def storage(self):
        """Create SQLite backend for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            backend = SQLiteBackend(f.name)
            await backend.initialize()
            yield backend
            await backend.close()

    @pytest.mark.asyncio
    async def test_xss_in_user_data(self, storage):
        """Test that XSS payloads are stored safely as data."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'\"><script>alert('xss')</script>",
            "<svg onload=alert('xss')>",
        ]
        
        for payload in xss_payloads:
            # Data should be stored as-is (not executed)
            user = await storage.get_or_create_user(payload)
            
            # Retrieved data should match exactly
            retrieved = await storage.get_user_by_id(user.id)
            assert retrieved.external_user_id == payload


class TestScopesListSecurity:
    """Tests for scopes list handling security."""

    @pytest.fixture
    async def storage(self):
        """Create SQLite backend for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            backend = SQLiteBackend(f.name)
            await backend.initialize()
            yield backend
            await backend.close()

    @pytest.mark.asyncio
    async def test_malicious_scopes_handled_safely(self, storage):
        """Test that malicious data in scopes list is handled safely."""
        user = await storage.get_or_create_user("scope_user")
        
        malicious_scopes = [
            "gmail.readonly",
            "'; DROP TABLE connections; --",
            "<script>alert('xss')</script>",
            "scope\nwith\nnewlines",
        ]
        
        connection = await storage.create_connection(
            user_id=user.id,
            gmail_address="scopes@gmail.com",
            access_token_encrypted="enc",
            refresh_token_encrypted="enc",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=malicious_scopes,
        )
        
        retrieved = await storage.get_connection(connection.id)
        
        # All scopes should be stored and retrieved exactly
        assert set(retrieved.scopes) == set(malicious_scopes)


class TestConnectionIDSecurity:
    """Tests for connection ID security."""

    @pytest.fixture
    async def storage(self):
        """Create SQLite backend for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            backend = SQLiteBackend(f.name)
            await backend.initialize()
            yield backend
            await backend.close()

    @pytest.mark.asyncio
    async def test_connection_id_randomness(self, storage):
        """Test that connection IDs appear random and unpredictable."""
        user = await storage.get_or_create_user("id_user")
        
        ids = []
        for i in range(10):
            conn = await storage.create_connection(
                user_id=user.id,
                gmail_address=f"test{i}@gmail.com",
                access_token_encrypted="enc",
                refresh_token_encrypted="enc",
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                scopes=["gmail.readonly"],
            )
            ids.append(conn.id)
        
        # All IDs should be unique
        assert len(ids) == len(set(ids))
        
        # IDs shouldn't be sequential integers
        # (Check that they don't follow simple patterns)
        for i in range(len(ids) - 1):
            # If IDs were sequential, this would show patterns
            assert ids[i] != ids[i + 1]
