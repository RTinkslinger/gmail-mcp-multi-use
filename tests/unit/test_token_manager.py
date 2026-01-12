"""Additional tests for TokenManager."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from gmail_multi_user.exceptions import (
    ConnectionInactiveError,
    ConnectionNotFoundError,
    TokenError,
)
from gmail_multi_user.tokens.manager import TokenManager
from gmail_multi_user.types import Connection


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = MagicMock()
    config.token_refresh_buffer_seconds = 300
    config.google = MagicMock()
    return config


@pytest.fixture
def mock_storage():
    """Create mock storage backend."""
    return AsyncMock()


@pytest.fixture
def mock_encryption():
    """Create mock encryption."""
    encryption = MagicMock()
    encryption.encrypt.return_value = "encrypted_token"
    encryption.decrypt.return_value = "decrypted_access_token"
    return encryption


@pytest.fixture
def mock_google_client():
    """Create mock Google OAuth client."""
    return AsyncMock()


@pytest.fixture
def token_manager(mock_config, mock_storage, mock_encryption):
    """Create TokenManager with mocked dependencies."""
    return TokenManager(mock_config, mock_storage, mock_encryption)


@pytest.fixture
def valid_connection():
    """Create a valid connection."""
    return Connection(
        id="conn_123",
        user_id="user_123",
        gmail_address="user@gmail.com",
        access_token_encrypted="encrypted_access",
        refresh_token_encrypted="encrypted_refresh",
        token_expires_at=datetime.utcnow() + timedelta(hours=1),
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_used_at=None,
    )


@pytest.fixture
def expiring_connection():
    """Create a connection with expiring token."""
    return Connection(
        id="conn_123",
        user_id="user_123",
        gmail_address="user@gmail.com",
        access_token_encrypted="encrypted_access",
        refresh_token_encrypted="encrypted_refresh",
        token_expires_at=datetime.utcnow() + timedelta(minutes=2),  # Within buffer
        scopes=["https://www.googleapis.com/auth/gmail.readonly"],
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_used_at=None,
    )


class TestGetValidToken:
    """Tests for get_valid_token."""

    @pytest.mark.asyncio
    async def test_get_valid_token_success(self, token_manager, mock_storage, valid_connection):
        """Test getting valid token without refresh."""
        mock_storage.get_connection.return_value = valid_connection

        result = await token_manager.get_valid_token("conn_123")

        assert result.access_token == "decrypted_access_token"
        assert result.connection_id == "conn_123"
        assert result.gmail_address == "user@gmail.com"
        mock_storage.update_connection_last_used.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_refreshes_expiring(
        self, token_manager, mock_storage, mock_encryption, expiring_connection
    ):
        """Test token is refreshed when expiring soon."""
        mock_storage.get_connection.return_value = expiring_connection

        # Mock Google client for refresh
        token_manager._google_client = AsyncMock()
        token_manager._google_client.refresh_access_token.return_value = MagicMock(
            access_token="new_access_token",
            refresh_token=None,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        # Mock storage update
        updated_connection = Connection(
            **{**expiring_connection.__dict__, "token_expires_at": datetime.utcnow() + timedelta(hours=1)}
        )
        mock_storage.update_connection_tokens.return_value = updated_connection

        result = await token_manager.get_valid_token("conn_123")

        assert result.access_token == "decrypted_access_token"
        token_manager._google_client.refresh_access_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_connection_not_found(self, token_manager, mock_storage):
        """Test error when connection not found."""
        mock_storage.get_connection.return_value = None

        with pytest.raises(ConnectionNotFoundError):
            await token_manager.get_valid_token("nonexistent")

    @pytest.mark.asyncio
    async def test_get_valid_token_connection_inactive(self, token_manager, mock_storage):
        """Test error when connection is inactive."""
        inactive_connection = Connection(
            id="conn_123",
            user_id="user_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=[],
            is_active=False,  # Inactive
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_connection.return_value = inactive_connection

        with pytest.raises(ConnectionInactiveError):
            await token_manager.get_valid_token("conn_123")


class TestRefreshToken:
    """Tests for refresh_token."""

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, token_manager, mock_storage, mock_encryption, valid_connection):
        """Test force refreshing token."""
        mock_storage.get_connection.return_value = valid_connection

        token_manager._google_client = AsyncMock()
        token_manager._google_client.refresh_access_token.return_value = MagicMock(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        mock_storage.update_connection_tokens.return_value = valid_connection

        result = await token_manager.refresh_token("conn_123")

        assert result.access_token == "decrypted_access_token"
        token_manager._google_client.refresh_access_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_not_found(self, token_manager, mock_storage):
        """Test refresh when connection not found."""
        mock_storage.get_connection.return_value = None

        with pytest.raises(ConnectionNotFoundError):
            await token_manager.refresh_token("nonexistent")


class TestRefreshExpiringTokens:
    """Tests for refresh_expiring_tokens."""

    @pytest.mark.asyncio
    async def test_refresh_expiring_tokens(self, token_manager, mock_storage, mock_encryption):
        """Test batch refreshing expiring tokens."""
        expiring_connections = [
            Connection(
                id=f"conn_{i}",
                user_id=f"user_{i}",
                gmail_address=f"user{i}@gmail.com",
                access_token_encrypted="encrypted",
                refresh_token_encrypted="encrypted",
                token_expires_at=datetime.utcnow() + timedelta(minutes=2),
                scopes=[],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_used_at=None,
            )
            for i in range(3)
        ]
        mock_storage.get_expiring_connections.return_value = expiring_connections

        token_manager._google_client = AsyncMock()
        token_manager._google_client.refresh_access_token.return_value = MagicMock(
            access_token="new_token",
            refresh_token=None,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        mock_storage.update_connection_tokens.return_value = expiring_connections[0]

        refreshed = await token_manager.refresh_expiring_tokens()

        assert len(refreshed) == 3
        assert token_manager._google_client.refresh_access_token.call_count == 3

    @pytest.mark.asyncio
    async def test_refresh_expiring_tokens_marks_failed_inactive(self, token_manager, mock_storage, mock_encryption):
        """Test that failed refreshes deactivate connections."""
        expiring_connections = [
            Connection(
                id="conn_1",
                user_id="user_1",
                gmail_address="user@gmail.com",
                access_token_encrypted="encrypted",
                refresh_token_encrypted="encrypted",
                token_expires_at=datetime.utcnow() + timedelta(minutes=2),
                scopes=[],
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_used_at=None,
            )
        ]
        mock_storage.get_expiring_connections.return_value = expiring_connections

        token_manager._google_client = AsyncMock()
        token_manager._google_client.refresh_access_token.side_effect = TokenError(
            message="Token revoked",
            code="token_revoked",
        )

        refreshed = await token_manager.refresh_expiring_tokens()

        assert len(refreshed) == 0
        mock_storage.deactivate_connection.assert_called_once_with("conn_1")


class TestInternalRefreshToken:
    """Tests for _refresh_token internal method."""

    @pytest.mark.asyncio
    async def test_refresh_token_encryption_error(self, token_manager, mock_encryption, valid_connection):
        """Test handling encryption errors during refresh."""
        mock_encryption.decrypt.side_effect = Exception("Decryption failed")

        with pytest.raises(TokenError) as exc_info:
            await token_manager._refresh_token(valid_connection)

        assert exc_info.value.code == "encryption_error"

    @pytest.mark.asyncio
    async def test_refresh_token_no_refresh_token(self, token_manager, mock_encryption, valid_connection):
        """Test error when no refresh token available."""
        mock_encryption.decrypt.return_value = ""  # Empty refresh token

        with pytest.raises(TokenError) as exc_info:
            await token_manager._refresh_token(valid_connection)

        assert exc_info.value.code == "needs_reauth"

    @pytest.mark.asyncio
    async def test_refresh_token_google_error(self, token_manager, mock_encryption, valid_connection):
        """Test handling Google API errors during refresh."""
        mock_encryption.decrypt.return_value = "valid_refresh_token"

        token_manager._google_client = AsyncMock()
        token_manager._google_client.refresh_access_token.side_effect = Exception("API error")

        with pytest.raises(TokenError) as exc_info:
            await token_manager._refresh_token(valid_connection)

        assert exc_info.value.code == "refresh_failed"

    @pytest.mark.asyncio
    async def test_refresh_token_updates_with_new_refresh(
        self, token_manager, mock_storage, mock_encryption, valid_connection
    ):
        """Test that new refresh token is stored."""
        mock_encryption.decrypt.return_value = "old_refresh_token"

        token_manager._google_client = AsyncMock()
        token_manager._google_client.refresh_access_token.return_value = MagicMock(
            access_token="new_access",
            refresh_token="new_refresh",  # New refresh token provided
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

        mock_storage.update_connection_tokens.return_value = valid_connection

        await token_manager._refresh_token(valid_connection)

        # Verify both tokens were encrypted
        assert mock_encryption.encrypt.call_count == 2


class TestNeedsRefresh:
    """Tests for _needs_refresh."""

    def test_needs_refresh_true(self, token_manager):
        """Test token needs refresh when within buffer."""
        connection = Connection(
            id="conn",
            user_id="user",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow() + timedelta(minutes=2),  # Within 5-min buffer
            scopes=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )

        assert token_manager._needs_refresh(connection) is True

    def test_needs_refresh_false(self, token_manager):
        """Test token doesn't need refresh when fresh."""
        connection = Connection(
            id="conn",
            user_id="user",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),  # Well beyond buffer
            scopes=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )

        assert token_manager._needs_refresh(connection) is False


class TestCheckConnectionValid:
    """Tests for check_connection_valid."""

    @pytest.mark.asyncio
    async def test_check_connection_valid_success(self, token_manager, mock_storage, valid_connection):
        """Test checking valid connection."""
        mock_storage.get_connection.return_value = valid_connection

        result = await token_manager.check_connection_valid("conn_123")

        assert result is True

    @pytest.mark.asyncio
    async def test_check_connection_valid_not_found(self, token_manager, mock_storage):
        """Test checking non-existent connection."""
        mock_storage.get_connection.return_value = None

        result = await token_manager.check_connection_valid("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_check_connection_valid_inactive(self, token_manager, mock_storage):
        """Test checking inactive connection."""
        inactive_connection = Connection(
            id="conn_123",
            user_id="user_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=[],
            is_active=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_connection.return_value = inactive_connection

        result = await token_manager.check_connection_valid("conn_123")

        assert result is False


class TestClose:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    async def test_close(self, token_manager):
        """Test closing token manager resources."""
        token_manager._google_client = AsyncMock()

        await token_manager.close()

        token_manager._google_client.close.assert_called_once()
