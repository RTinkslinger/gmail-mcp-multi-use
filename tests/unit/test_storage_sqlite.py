"""Tests for SQLite storage backend."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from gmail_multi_user.exceptions import StorageError
from gmail_multi_user.storage.sqlite import SQLiteBackend


class TestSQLiteBackendLifecycle:
    """Tests for SQLite backend lifecycle methods."""

    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self) -> None:
        """Test that initialize creates required tables."""
        backend = SQLiteBackend(":memory:")
        await backend.initialize()

        # Should be able to query tables
        conn = await backend._get_connection()
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ) as cursor:
            tables = {row[0] for row in await cursor.fetchall()}

        assert "users" in tables
        assert "gmail_connections" in tables
        assert "oauth_states" in tables
        assert "schema_migrations" in tables

        await backend.close()

    @pytest.mark.asyncio
    async def test_health_check_returns_true_when_healthy(
        self,
        sqlite_backend: SQLiteBackend,
    ) -> None:
        """Test that health_check returns True for healthy connection."""
        result = await sqlite_backend.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_close_closes_connection(self) -> None:
        """Test that close closes the database connection."""
        backend = SQLiteBackend(":memory:")
        await backend.initialize()
        await backend.close()

        # Connection should be None after close
        assert backend._connection is None


class TestSQLiteBackendUsers:
    """Tests for SQLite backend user operations."""

    @pytest.mark.asyncio
    async def test_get_or_create_user_creates_new_user(
        self,
        sqlite_backend: SQLiteBackend,
        test_user_data: dict,
    ) -> None:
        """Test creating a new user."""
        user = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
            email=test_user_data["email"],
        )

        assert user.external_user_id == test_user_data["external_user_id"]
        assert user.email == test_user_data["email"]
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_or_create_user_returns_existing(
        self,
        sqlite_backend: SQLiteBackend,
        test_user_data: dict,
    ) -> None:
        """Test that get_or_create returns existing user."""
        # Create first
        user1 = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
            email=test_user_data["email"],
        )

        # Get again
        user2 = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
        )

        assert user1.id == user2.id
        assert user2.email == test_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_or_create_user_updates_email(
        self,
        sqlite_backend: SQLiteBackend,
        test_user_data: dict,
    ) -> None:
        """Test that get_or_create updates email if provided."""
        # Create with original email
        user1 = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
            email=test_user_data["email"],
        )

        # Update with new email
        new_email = "newemail@example.com"
        user2 = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
            email=new_email,
        )

        assert user1.id == user2.id
        assert user2.email == new_email

    @pytest.mark.asyncio
    async def test_get_user_by_external_id(
        self,
        sqlite_backend: SQLiteBackend,
        test_user_data: dict,
    ) -> None:
        """Test getting user by external ID."""
        # Create user
        created = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
            email=test_user_data["email"],
        )

        # Fetch by external ID
        fetched = await sqlite_backend.get_user_by_external_id(
            test_user_data["external_user_id"]
        )

        assert fetched is not None
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_user_by_external_id_not_found(
        self,
        sqlite_backend: SQLiteBackend,
    ) -> None:
        """Test getting non-existent user returns None."""
        user = await sqlite_backend.get_user_by_external_id("nonexistent_id")
        assert user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self,
        sqlite_backend: SQLiteBackend,
        test_user_data: dict,
    ) -> None:
        """Test getting user by internal ID."""
        created = await sqlite_backend.get_or_create_user(
            external_user_id=test_user_data["external_user_id"],
        )

        fetched = await sqlite_backend.get_user_by_id(created.id)

        assert fetched is not None
        assert fetched.external_user_id == test_user_data["external_user_id"]

    @pytest.mark.asyncio
    async def test_list_users(
        self,
        sqlite_backend: SQLiteBackend,
    ) -> None:
        """Test listing all users."""
        # Create multiple users
        await sqlite_backend.get_or_create_user(external_user_id="user_1")
        await sqlite_backend.get_or_create_user(external_user_id="user_2")
        await sqlite_backend.get_or_create_user(external_user_id="user_3")

        users = await sqlite_backend.list_users()

        assert len(users) == 3


class TestSQLiteBackendConnections:
    """Tests for SQLite backend connection operations."""

    @pytest.mark.asyncio
    async def test_create_connection(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test creating a connection."""
        backend, user_id = sqlite_backend_with_user

        connection = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        assert connection.id is not None
        assert connection.user_id == user_id
        assert connection.gmail_address == test_connection_data["gmail_address"]
        assert connection.is_active is True
        assert connection.scopes == test_connection_data["scopes"]

    @pytest.mark.asyncio
    async def test_create_duplicate_connection_raises_error(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test that creating duplicate connection raises error."""
        backend, user_id = sqlite_backend_with_user

        # Create first connection
        await backend.create_connection(user_id=user_id, **test_connection_data)

        # Try to create duplicate
        with pytest.raises(StorageError):
            await backend.create_connection(user_id=user_id, **test_connection_data)

    @pytest.mark.asyncio
    async def test_get_connection(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test getting a connection by ID."""
        backend, user_id = sqlite_backend_with_user

        created = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        fetched = await backend.get_connection(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.gmail_address == created.gmail_address

    @pytest.mark.asyncio
    async def test_get_connection_not_found(
        self,
        sqlite_backend: SQLiteBackend,
    ) -> None:
        """Test getting non-existent connection returns None."""
        connection = await sqlite_backend.get_connection("nonexistent_id")
        assert connection is None

    @pytest.mark.asyncio
    async def test_get_connection_by_user_and_email(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test getting connection by user and email."""
        backend, user_id = sqlite_backend_with_user

        created = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        fetched = await backend.get_connection_by_user_and_email(
            user_id=user_id,
            gmail_address=test_connection_data["gmail_address"],
        )

        assert fetched is not None
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_list_connections_all(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        token_encryptor,
    ) -> None:
        """Test listing all connections."""
        backend, user_id = sqlite_backend_with_user

        # Create multiple connections
        for i in range(3):
            await backend.create_connection(
                user_id=user_id,
                gmail_address=f"user{i}@gmail.com",
                access_token_encrypted=token_encryptor.encrypt("token"),
                refresh_token_encrypted=token_encryptor.encrypt("refresh"),
                token_expires_at=datetime.utcnow() + timedelta(hours=1),
                scopes=["gmail.readonly"],
            )

        connections = await backend.list_connections()

        assert len(connections) == 3

    @pytest.mark.asyncio
    async def test_list_connections_by_user(
        self,
        sqlite_backend: SQLiteBackend,
        token_encryptor,
    ) -> None:
        """Test listing connections filtered by user."""
        # Create two users
        user1 = await sqlite_backend.get_or_create_user(external_user_id="user1")
        user2 = await sqlite_backend.get_or_create_user(external_user_id="user2")

        # Create connections for each
        await sqlite_backend.create_connection(
            user_id=user1.id,
            gmail_address="user1@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh"),
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )
        await sqlite_backend.create_connection(
            user_id=user2.id,
            gmail_address="user2@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh"),
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        # List for user1 only
        connections = await sqlite_backend.list_connections(user_id=user1.id)

        assert len(connections) == 1
        assert connections[0].user_id == user1.id

    @pytest.mark.asyncio
    async def test_list_connections_excludes_inactive(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test that list_connections excludes inactive by default."""
        backend, user_id = sqlite_backend_with_user

        # Create and deactivate a connection
        connection = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )
        await backend.deactivate_connection(connection.id)

        # Should not appear in default list
        connections = await backend.list_connections()
        assert len(connections) == 0

        # Should appear when including inactive
        connections = await backend.list_connections(include_inactive=True)
        assert len(connections) == 1

    @pytest.mark.asyncio
    async def test_update_connection_tokens(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
        token_encryptor,
    ) -> None:
        """Test updating connection tokens."""
        backend, user_id = sqlite_backend_with_user

        connection = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        new_access_token = token_encryptor.encrypt("new_access_token")
        new_refresh_token = token_encryptor.encrypt("new_refresh_token")
        new_expires = datetime.utcnow() + timedelta(hours=2)

        updated = await backend.update_connection_tokens(
            connection_id=connection.id,
            access_token_encrypted=new_access_token,
            refresh_token_encrypted=new_refresh_token,
            token_expires_at=new_expires,
        )

        assert updated.access_token_encrypted == new_access_token
        assert updated.refresh_token_encrypted == new_refresh_token

    @pytest.mark.asyncio
    async def test_deactivate_connection(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test deactivating a connection."""
        backend, user_id = sqlite_backend_with_user

        connection = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        await backend.deactivate_connection(connection.id)

        updated = await backend.get_connection(connection.id)
        assert updated is not None
        assert updated.is_active is False

    @pytest.mark.asyncio
    async def test_delete_connection(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_connection_data: dict,
    ) -> None:
        """Test deleting a connection."""
        backend, user_id = sqlite_backend_with_user

        connection = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        await backend.delete_connection(connection.id)

        deleted = await backend.get_connection(connection.id)
        assert deleted is None

    @pytest.mark.asyncio
    async def test_get_expiring_connections(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        token_encryptor,
    ) -> None:
        """Test getting connections with expiring tokens."""
        backend, user_id = sqlite_backend_with_user

        # Create connection expiring soon
        await backend.create_connection(
            user_id=user_id,
            gmail_address="expiring@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh"),
            token_expires_at=datetime.utcnow() + timedelta(minutes=2),
            scopes=["gmail.readonly"],
        )

        # Create connection not expiring soon
        await backend.create_connection(
            user_id=user_id,
            gmail_address="notexpiring@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh"),
            token_expires_at=datetime.utcnow() + timedelta(hours=2),
            scopes=["gmail.readonly"],
        )

        # Get connections expiring in next 5 minutes
        expires_before = datetime.utcnow() + timedelta(minutes=5)
        expiring = await backend.get_expiring_connections(expires_before)

        assert len(expiring) == 1
        assert expiring[0].gmail_address == "expiring@gmail.com"


class TestSQLiteBackendOAuthStates:
    """Tests for SQLite backend OAuth state operations."""

    @pytest.mark.asyncio
    async def test_create_oauth_state(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_oauth_state_data: dict,
    ) -> None:
        """Test creating an OAuth state."""
        backend, user_id = sqlite_backend_with_user

        state = await backend.create_oauth_state(
            user_id=user_id,
            **test_oauth_state_data,
        )

        assert state.id is not None
        assert state.state == test_oauth_state_data["state"]
        assert state.user_id == user_id
        assert state.scopes == test_oauth_state_data["scopes"]

    @pytest.mark.asyncio
    async def test_get_oauth_state(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_oauth_state_data: dict,
    ) -> None:
        """Test getting an OAuth state by state string."""
        backend, user_id = sqlite_backend_with_user

        created = await backend.create_oauth_state(
            user_id=user_id,
            **test_oauth_state_data,
        )

        fetched = await backend.get_oauth_state(test_oauth_state_data["state"])

        assert fetched is not None
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_get_oauth_state_not_found(
        self,
        sqlite_backend: SQLiteBackend,
    ) -> None:
        """Test getting non-existent OAuth state returns None."""
        state = await sqlite_backend.get_oauth_state("nonexistent_state")
        assert state is None

    @pytest.mark.asyncio
    async def test_delete_oauth_state(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
        test_oauth_state_data: dict,
    ) -> None:
        """Test deleting an OAuth state."""
        backend, user_id = sqlite_backend_with_user

        await backend.create_oauth_state(
            user_id=user_id,
            **test_oauth_state_data,
        )

        await backend.delete_oauth_state(test_oauth_state_data["state"])

        deleted = await backend.get_oauth_state(test_oauth_state_data["state"])
        assert deleted is None

    @pytest.mark.asyncio
    async def test_cleanup_expired_states(
        self,
        sqlite_backend_with_user: tuple[SQLiteBackend, str],
    ) -> None:
        """Test cleaning up expired OAuth states."""
        backend, user_id = sqlite_backend_with_user

        # Create expired state
        await backend.create_oauth_state(
            user_id=user_id,
            state="expired_state",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="verifier",
            expires_at=datetime.utcnow() - timedelta(minutes=5),  # Already expired
        )

        # Create valid state
        await backend.create_oauth_state(
            user_id=user_id,
            state="valid_state",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
            code_verifier="verifier",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
        )

        # Cleanup
        deleted_count = await backend.cleanup_expired_states()

        assert deleted_count == 1

        # Verify
        expired = await backend.get_oauth_state("expired_state")
        valid = await backend.get_oauth_state("valid_state")

        assert expired is None
        assert valid is not None
