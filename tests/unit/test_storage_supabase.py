"""Unit tests for Supabase storage backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from gmail_multi_user.exceptions import StorageError
from gmail_multi_user.storage.supabase import SupabaseBackend


@pytest.fixture
def mock_supabase_client() -> MagicMock:
    """Create a mock Supabase client."""
    return MagicMock()


@pytest.fixture
def backend(mock_supabase_client: MagicMock) -> SupabaseBackend:
    """Create a SupabaseBackend with mocked client."""
    backend = SupabaseBackend(
        supabase_url="https://test.supabase.co",
        supabase_key="test_key",
    )
    backend._client = mock_supabase_client
    return backend


def create_mock_response(
    data: list[dict[str, Any]] | None = None, count: int | None = None
) -> MagicMock:
    """Create a mock Supabase response."""
    response = MagicMock()
    response.data = data or []
    response.count = count
    return response


class TestSupabaseBackendLifecycle:
    """Tests for lifecycle methods."""

    @pytest.mark.asyncio
    async def test_initialize_success(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test successful initialization."""
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = create_mock_response(
            [{"id": "1"}]
        )

        await backend.initialize()

        mock_supabase_client.table.assert_called_with("users")

    @pytest.mark.asyncio
    async def test_initialize_connection_failed(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test initialization failure."""
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "Connection failed"
        )

        with pytest.raises(StorageError) as exc_info:
            await backend.initialize()

        assert exc_info.value.code == "connection_failed"

    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test health check returns True when healthy."""
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.return_value = create_mock_response(
            [{"id": "1"}]
        )

        result = await backend.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test health check returns False when unhealthy."""
        mock_supabase_client.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception(
            "Connection failed"
        )

        result = await backend.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, backend: SupabaseBackend) -> None:
        """Test close clears client."""
        await backend.close()
        assert backend._client is None


class TestSupabaseBackendUsers:
    """Tests for user operations."""

    @pytest.mark.asyncio
    async def test_get_or_create_user_creates_new(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test creating a new user."""
        now = datetime.now(timezone.utc).isoformat()

        # First query returns empty (user doesn't exist)
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            []
        )

        # Insert returns new user
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "user123",
                    "external_user_id": "ext_123",
                    "email": "test@example.com",
                    "created_at": now,
                    "updated_at": now,
                }
            ]
        )

        user = await backend.get_or_create_user("ext_123", "test@example.com")

        assert user.id == "user123"
        assert user.external_user_id == "ext_123"
        assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_or_create_user_returns_existing(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test returning existing user."""
        now = datetime.now(timezone.utc).isoformat()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "user123",
                    "external_user_id": "ext_123",
                    "email": "test@example.com",
                    "created_at": now,
                    "updated_at": now,
                }
            ]
        )

        user = await backend.get_or_create_user("ext_123")

        assert user.id == "user123"
        assert user.external_user_id == "ext_123"

    @pytest.mark.asyncio
    async def test_get_user_by_external_id(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test getting user by external ID."""
        now = datetime.now(timezone.utc).isoformat()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "user123",
                    "external_user_id": "ext_123",
                    "email": "test@example.com",
                    "created_at": now,
                    "updated_at": now,
                }
            ]
        )

        user = await backend.get_user_by_external_id("ext_123")

        assert user is not None
        assert user.external_user_id == "ext_123"

    @pytest.mark.asyncio
    async def test_get_user_by_external_id_not_found(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test getting non-existent user returns None."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            []
        )

        user = await backend.get_user_by_external_id("nonexistent")

        assert user is None

    @pytest.mark.asyncio
    async def test_list_users(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test listing all users."""
        now = datetime.now(timezone.utc).isoformat()

        mock_supabase_client.table.return_value.select.return_value.order.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "user1",
                    "external_user_id": "ext_1",
                    "email": "user1@example.com",
                    "created_at": now,
                    "updated_at": now,
                },
                {
                    "id": "user2",
                    "external_user_id": "ext_2",
                    "email": "user2@example.com",
                    "created_at": now,
                    "updated_at": now,
                },
            ]
        )

        users = await backend.list_users()

        assert len(users) == 2
        assert users[0].id == "user1"
        assert users[1].id == "user2"


class TestSupabaseBackendConnections:
    """Tests for connection operations."""

    @pytest.mark.asyncio
    async def test_create_connection(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test creating a connection."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires = now + timedelta(hours=1)

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "conn123",
                    "user_id": "user123",
                    "gmail_address": "test@gmail.com",
                    "access_token_encrypted": "enc_access",
                    "refresh_token_encrypted": "enc_refresh",
                    "token_expires_at": expires.isoformat(),
                    "scopes": '["gmail.readonly"]',
                    "is_active": True,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "last_used_at": None,
                }
            ]
        )

        connection = await backend.create_connection(
            user_id="user123",
            gmail_address="test@gmail.com",
            access_token_encrypted="enc_access",
            refresh_token_encrypted="enc_refresh",
            token_expires_at=expires,
            scopes=["gmail.readonly"],
        )

        assert connection.id == "conn123"
        assert connection.gmail_address == "test@gmail.com"
        assert connection.is_active is True

    @pytest.mark.asyncio
    async def test_create_connection_duplicate_raises_error(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test duplicate connection raises StorageError."""
        mock_supabase_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "unique constraint violated"
        )

        with pytest.raises(StorageError) as exc_info:
            await backend.create_connection(
                user_id="user123",
                gmail_address="test@gmail.com",
                access_token_encrypted="enc_access",
                refresh_token_encrypted="enc_refresh",
                token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                scopes=["gmail.readonly"],
            )

        assert exc_info.value.code == "query_failed"

    @pytest.mark.asyncio
    async def test_get_connection(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test getting a connection."""
        now = datetime.now(timezone.utc).isoformat()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "conn123",
                    "user_id": "user123",
                    "gmail_address": "test@gmail.com",
                    "access_token_encrypted": "enc_access",
                    "refresh_token_encrypted": "enc_refresh",
                    "token_expires_at": now,
                    "scopes": '["gmail.readonly"]',
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                    "last_used_at": None,
                }
            ]
        )

        connection = await backend.get_connection("conn123")

        assert connection is not None
        assert connection.id == "conn123"

    @pytest.mark.asyncio
    async def test_get_connection_not_found(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test getting non-existent connection returns None."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            []
        )

        connection = await backend.get_connection("nonexistent")

        assert connection is None

    @pytest.mark.asyncio
    async def test_list_connections(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test listing connections."""
        now = datetime.now(timezone.utc).isoformat()

        mock_query = MagicMock()
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "conn1",
                    "user_id": "user123",
                    "gmail_address": "test1@gmail.com",
                    "access_token_encrypted": "enc_access",
                    "refresh_token_encrypted": "enc_refresh",
                    "token_expires_at": now,
                    "scopes": '["gmail.readonly"]',
                    "is_active": True,
                    "created_at": now,
                    "updated_at": now,
                    "last_used_at": None,
                },
            ]
        )
        mock_supabase_client.table.return_value.select.return_value = mock_query

        connections = await backend.list_connections()

        assert len(connections) == 1
        assert connections[0].id == "conn1"

    @pytest.mark.asyncio
    async def test_update_connection_tokens(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test updating connection tokens."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        new_expires = now + timedelta(hours=1)

        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "conn123",
                    "user_id": "user123",
                    "gmail_address": "test@gmail.com",
                    "access_token_encrypted": "new_enc_access",
                    "refresh_token_encrypted": "new_enc_refresh",
                    "token_expires_at": new_expires.isoformat(),
                    "scopes": '["gmail.readonly"]',
                    "is_active": True,
                    "created_at": now_iso,
                    "updated_at": now_iso,
                    "last_used_at": None,
                }
            ]
        )

        connection = await backend.update_connection_tokens(
            connection_id="conn123",
            access_token_encrypted="new_enc_access",
            refresh_token_encrypted="new_enc_refresh",
            token_expires_at=new_expires,
        )

        assert connection.access_token_encrypted == "new_enc_access"

    @pytest.mark.asyncio
    async def test_deactivate_connection(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test deactivating a connection."""
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = create_mock_response(
            [{"id": "conn123", "is_active": False}]
        )

        await backend.deactivate_connection("conn123")

        mock_supabase_client.table.return_value.update.assert_called()

    @pytest.mark.asyncio
    async def test_delete_connection(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test deleting a connection."""
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = create_mock_response(
            []
        )

        await backend.delete_connection("conn123")

        mock_supabase_client.table.return_value.delete.assert_called()


class TestSupabaseBackendOAuthStates:
    """Tests for OAuth state operations."""

    @pytest.mark.asyncio
    async def test_create_oauth_state(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test creating an OAuth state."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        expires = now + timedelta(minutes=10)

        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "state_id",
                    "state": "state123",
                    "user_id": "user123",
                    "scopes": '["gmail.readonly"]',
                    "redirect_uri": "http://localhost:8080/callback",
                    "code_verifier": "verifier123",
                    "expires_at": expires.isoformat(),
                    "created_at": now_iso,
                }
            ]
        )

        state = await backend.create_oauth_state(
            state="state123",
            user_id="user123",
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8080/callback",
            code_verifier="verifier123",
            expires_at=expires,
        )

        assert state.state == "state123"
        assert state.user_id == "user123"

    @pytest.mark.asyncio
    async def test_get_oauth_state(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test getting an OAuth state."""
        now = datetime.now(timezone.utc).isoformat()

        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            [
                {
                    "id": "state_id",
                    "state": "state123",
                    "user_id": "user123",
                    "scopes": '["gmail.readonly"]',
                    "redirect_uri": "http://localhost:8080/callback",
                    "code_verifier": "verifier123",
                    "expires_at": now,
                    "created_at": now,
                }
            ]
        )

        state = await backend.get_oauth_state("state123")

        assert state is not None
        assert state.state == "state123"

    @pytest.mark.asyncio
    async def test_get_oauth_state_not_found(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test getting non-existent OAuth state."""
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = create_mock_response(
            []
        )

        state = await backend.get_oauth_state("nonexistent")

        assert state is None

    @pytest.mark.asyncio
    async def test_delete_oauth_state(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test deleting an OAuth state."""
        mock_supabase_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = create_mock_response(
            []
        )

        await backend.delete_oauth_state("state123")

        mock_supabase_client.table.return_value.delete.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_expired_states(
        self,
        backend: SupabaseBackend,
        mock_supabase_client: MagicMock,
    ) -> None:
        """Test cleaning up expired states."""
        # Count query
        mock_supabase_client.table.return_value.select.return_value.lt.return_value.execute.return_value = create_mock_response(
            [], count=3
        )

        # Delete query
        mock_supabase_client.table.return_value.delete.return_value.lt.return_value.execute.return_value = create_mock_response(
            []
        )

        count = await backend.cleanup_expired_states()

        assert count == 3
