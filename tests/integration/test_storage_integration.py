"""Integration tests for storage backends.

These tests use real SQLite database files to verify
storage operations work correctly end-to-end.
"""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta

import pytest

from gmail_multi_user.storage.sqlite import SQLiteBackend


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup happens via context manager


@pytest.fixture
async def storage(temp_db):
    """Create SQLite backend with temp database."""
    backend = SQLiteBackend(temp_db)
    await backend.initialize()
    yield backend
    await backend.close()


class TestUserStorage:
    """Integration tests for user storage."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_user(self, storage):
        """Test creating and retrieving a user."""
        user = await storage.get_or_create_user("external_user_123")

        assert user.external_user_id == "external_user_123"
        assert user.id is not None

        # Retrieve again - should get same user
        same_user = await storage.get_or_create_user("external_user_123")
        assert same_user.id == user.id

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, storage):
        """Test retrieving user by internal ID."""
        user = await storage.get_or_create_user("external_456")

        retrieved = await storage.get_user_by_id(user.id)

        assert retrieved is not None
        assert retrieved.id == user.id
        assert retrieved.external_user_id == "external_456"

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, storage):
        """Test retrieving non-existent user returns None."""
        result = await storage.get_user_by_id("nonexistent")
        assert result is None


class TestConnectionStorage:
    """Integration tests for connection storage."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_connection(self, storage):
        """Test creating and retrieving a connection."""
        user = await storage.get_or_create_user("user_123")

        connection = await storage.create_connection(
            user_id=user.id,
            gmail_address="test@gmail.com",
            access_token_encrypted="enc_access",
            refresh_token_encrypted="enc_refresh",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        assert connection.id is not None
        assert connection.gmail_address == "test@gmail.com"
        assert connection.is_active is True

        # Retrieve by ID
        retrieved = await storage.get_connection(connection.id)
        assert retrieved is not None
        assert retrieved.id == connection.id

    @pytest.mark.asyncio
    async def test_get_connection_by_user_and_email(self, storage):
        """Test retrieving connection by user and email."""
        user = await storage.get_or_create_user("user_456")

        await storage.create_connection(
            user_id=user.id,
            gmail_address="specific@gmail.com",
            access_token_encrypted="enc",
            refresh_token_encrypted="enc",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        found = await storage.get_connection_by_user_and_email(
            user.id, "specific@gmail.com"
        )

        assert found is not None
        assert found.gmail_address == "specific@gmail.com"

    @pytest.mark.asyncio
    async def test_list_user_connections(self, storage):
        """Test listing all connections for a user."""
        user = await storage.get_or_create_user("multi_user")

        # Create multiple connections
        for i in range(3):
            await storage.create_connection(
                user_id=user.id,
                gmail_address=f"email{i}@gmail.com",
                access_token_encrypted="enc",
                refresh_token_encrypted="enc",
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                scopes=["gmail.readonly"],
            )

        connections = await storage.list_connections(user_id=user.id)

        assert len(connections) == 3

    @pytest.mark.asyncio
    async def test_update_connection_tokens(self, storage):
        """Test updating connection tokens."""
        user = await storage.get_or_create_user("token_user")

        connection = await storage.create_connection(
            user_id=user.id,
            gmail_address="token@gmail.com",
            access_token_encrypted="old_access",
            refresh_token_encrypted="old_refresh",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        new_expires = datetime.utcnow() + timedelta(hours=2)
        updated = await storage.update_connection_tokens(
            connection_id=connection.id,
            access_token_encrypted="new_access",
            refresh_token_encrypted="new_refresh",
            token_expires_at=new_expires,
        )

        assert updated.access_token_encrypted == "new_access"
        assert updated.refresh_token_encrypted == "new_refresh"

    @pytest.mark.asyncio
    async def test_deactivate_connection(self, storage):
        """Test deactivating a connection."""
        user = await storage.get_or_create_user("deact_user")

        connection = await storage.create_connection(
            user_id=user.id,
            gmail_address="deact@gmail.com",
            access_token_encrypted="enc",
            refresh_token_encrypted="enc",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        assert connection.is_active is True

        await storage.deactivate_connection(connection.id)

        deactivated = await storage.get_connection(connection.id)
        assert deactivated.is_active is False

    @pytest.mark.asyncio
    async def test_get_expiring_connections(self, storage):
        """Test retrieving connections with expiring tokens."""
        user = await storage.get_or_create_user("expiring_user")

        # Create expiring connection
        await storage.create_connection(
            user_id=user.id,
            gmail_address="expiring@gmail.com",
            access_token_encrypted="enc",
            refresh_token_encrypted="enc",
            token_expires_at=datetime.utcnow() + timedelta(minutes=5),  # Expires soon
            scopes=["gmail.readonly"],
        )

        # Create non-expiring connection
        await storage.create_connection(
            user_id=user.id,
            gmail_address="fresh@gmail.com",
            access_token_encrypted="enc",
            refresh_token_encrypted="enc",
            token_expires_at=datetime.utcnow() + timedelta(hours=2),
            scopes=["gmail.readonly"],
        )

        # Get connections expiring before 10 minutes from now
        expires_before = datetime.utcnow() + timedelta(minutes=10)
        expiring = await storage.get_expiring_connections(expires_before=expires_before)

        # Should find the expiring one (5 min < 10 min threshold)
        assert len(expiring) >= 1
        assert any(c.gmail_address == "expiring@gmail.com" for c in expiring)


class TestOAuthStateStorage:
    """Integration tests for OAuth state storage."""

    @pytest.mark.asyncio
    async def test_create_and_retrieve_state(self, storage):
        """Test creating and retrieving OAuth state."""
        user = await storage.get_or_create_user("oauth_user")

        state = await storage.create_oauth_state(
            user_id=user.id,
            state="random_state_string",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="pkce_verifier",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        assert state.state == "random_state_string"
        assert state.code_verifier == "pkce_verifier"

        # Retrieve by state string
        retrieved = await storage.get_oauth_state("random_state_string")
        assert retrieved is not None
        assert retrieved.user_id == user.id

    @pytest.mark.asyncio
    async def test_delete_oauth_state(self, storage):
        """Test deleting OAuth state (single-use)."""
        user = await storage.get_or_create_user("state_user")

        state = await storage.create_oauth_state(
            user_id=user.id,
            state="to_delete",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="verifier",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        await storage.delete_oauth_state(state.state)

        deleted = await storage.get_oauth_state("to_delete")
        assert deleted is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_states(self, storage):
        """Test cleaning up expired OAuth states."""
        user = await storage.get_or_create_user("cleanup_user")

        # Create expired state
        await storage.create_oauth_state(
            user_id=user.id,
            state="expired_state",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="verifier",
            expires_at=datetime.utcnow() - timedelta(minutes=1),  # Already expired
        )

        # Create valid state
        await storage.create_oauth_state(
            user_id=user.id,
            state="valid_state",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="verifier",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
        )

        count = await storage.cleanup_expired_states()

        assert count >= 1

        # Expired should be gone
        expired = await storage.get_oauth_state("expired_state")
        assert expired is None

        # Valid should remain
        valid = await storage.get_oauth_state("valid_state")
        assert valid is not None


class TestTransactionIntegrity:
    """Tests for database transaction integrity."""

    @pytest.mark.asyncio
    async def test_connection_with_user_lookup(self, storage):
        """Test that connection can lookup user correctly."""
        user = await storage.get_or_create_user("integrity_user")

        connection = await storage.create_connection(
            user_id=user.id,
            gmail_address="integrity@gmail.com",
            access_token_encrypted="enc",
            refresh_token_encrypted="enc",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        # Get connection and verify user_id matches
        retrieved = await storage.get_connection(connection.id)
        found_user = await storage.get_user_by_id(retrieved.user_id)

        assert found_user.external_user_id == "integrity_user"
