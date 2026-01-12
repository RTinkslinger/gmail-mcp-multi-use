"""Tests for OAuth manager."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gmail_multi_user.exceptions import AuthError
from gmail_multi_user.oauth.manager import OAuthManager
from gmail_multi_user.types import OAuthState, Connection, User


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = MagicMock()
    config.oauth_state_ttl_seconds = 600
    config.google = MagicMock()
    config.google.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    config.google.redirect_uri = "http://localhost:8000/oauth/callback"
    return config


@pytest.fixture
def mock_storage():
    """Create mock storage backend."""
    storage = AsyncMock()
    storage.get_or_create_user.return_value = User(
        id="user_internal_123",
        external_user_id="user_external_123",
        email=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return storage


@pytest.fixture
def mock_encryption():
    """Create mock encryption."""
    encryption = MagicMock()
    encryption.encrypt.return_value = "encrypted_token"
    encryption.decrypt.return_value = "decrypted_token"
    return encryption


@pytest.fixture
def mock_state_manager():
    """Create mock state manager."""
    manager = AsyncMock()
    return manager


@pytest.fixture
def mock_google_client():
    """Create mock Google OAuth client."""
    client = AsyncMock()
    return client


@pytest.fixture
def oauth_manager(mock_config, mock_storage, mock_encryption):
    """Create OAuth manager with mocked dependencies."""
    return OAuthManager(mock_config, mock_storage, mock_encryption)


class TestGetAuthUrl:
    """Tests for get_auth_url."""

    @pytest.mark.asyncio
    async def test_get_auth_url_success(self, oauth_manager, mock_storage):
        """Test generating auth URL."""
        # Mock the internal state manager
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.create_state.return_value = OAuthState(
            id="state_id_123",
            state="test_state_123",
            user_id="user_internal_123",
            code_verifier="test_verifier",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            redirect_uri="http://localhost:8000/oauth/callback",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            created_at=datetime.utcnow(),
        )
        oauth_manager._state_manager.get_pkce_challenge.return_value = "test_challenge"

        oauth_manager._google_client = MagicMock()
        oauth_manager._google_client.build_auth_url.return_value = "https://accounts.google.com/oauth?state=test"

        result = await oauth_manager.get_auth_url(user_id="user_external_123")

        assert result.auth_url == "https://accounts.google.com/oauth?state=test"
        assert result.state == "test_state_123"
        mock_storage.get_or_create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_auth_url_custom_scopes(self, oauth_manager, mock_storage):
        """Test auth URL with custom scopes."""
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.create_state.return_value = OAuthState(
            id="state_id_456",
            state="test_state",
            user_id="user_internal_123",
            code_verifier="verifier",
            scopes=["https://www.googleapis.com/auth/gmail.modify"],
            redirect_uri="http://localhost:8000/oauth/callback",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            created_at=datetime.utcnow(),
        )
        oauth_manager._state_manager.get_pkce_challenge.return_value = "challenge"
        oauth_manager._google_client = MagicMock()
        oauth_manager._google_client.build_auth_url.return_value = "https://auth.url"

        custom_scopes = ["https://www.googleapis.com/auth/gmail.modify"]
        await oauth_manager.get_auth_url(user_id="user_123", scopes=custom_scopes)

        oauth_manager._state_manager.create_state.assert_called_once()
        call_args = oauth_manager._state_manager.create_state.call_args
        assert call_args.kwargs["scopes"] == custom_scopes


class TestHandleCallback:
    """Tests for handle_callback."""

    @pytest.mark.asyncio
    async def test_handle_callback_new_connection(self, oauth_manager, mock_storage, mock_encryption):
        """Test callback creates new connection."""
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.validate_and_consume.return_value = OAuthState(
            id="state_id_789",
            state="test_state",
            user_id="user_internal_123",
            code_verifier="verifier",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            redirect_uri="http://localhost:8000/oauth/callback",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            created_at=datetime.utcnow(),
        )

        oauth_manager._google_client = AsyncMock()
        oauth_manager._google_client.exchange_code.return_value = MagicMock(
            access_token="access_token_123",
            refresh_token="refresh_token_123",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        oauth_manager._google_client.get_user_info.return_value = MagicMock(
            email="user@gmail.com",
        )

        mock_storage.get_connection_by_user_and_email.return_value = None
        mock_storage.create_connection.return_value = Connection(
            id="conn_123",
            user_id="user_internal_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_user_by_id.return_value = User(
            id="user_internal_123",
            external_user_id="user_external_123",
            email=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await oauth_manager.handle_callback(code="auth_code", state="test_state")

        assert result.success is True
        assert result.connection_id == "conn_123"
        assert result.gmail_address == "user@gmail.com"
        mock_storage.create_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_callback_existing_connection(self, oauth_manager, mock_storage, mock_encryption):
        """Test callback updates existing connection."""
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.validate_and_consume.return_value = OAuthState(
            id="state_id_existing",
            state="test_state",
            user_id="user_internal_123",
            code_verifier="verifier",
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            redirect_uri="http://localhost:8000/oauth/callback",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            created_at=datetime.utcnow(),
        )

        oauth_manager._google_client = AsyncMock()
        oauth_manager._google_client.exchange_code.return_value = MagicMock(
            access_token="new_access_token",
            refresh_token="new_refresh_token",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        oauth_manager._google_client.get_user_info.return_value = MagicMock(
            email="user@gmail.com",
        )

        existing_connection = Connection(
            id="existing_conn",
            user_id="user_internal_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="old_encrypted",
            refresh_token_encrypted="old_encrypted",
            token_expires_at=datetime.utcnow() - timedelta(hours=1),
            scopes=["https://www.googleapis.com/auth/gmail.readonly"],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_connection_by_user_and_email.return_value = existing_connection
        mock_storage.update_connection_tokens.return_value = existing_connection
        mock_storage.get_user_by_id.return_value = User(
            id="user_internal_123",
            external_user_id="user_external_123",
            email=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        result = await oauth_manager.handle_callback(code="auth_code", state="test_state")

        assert result.success is True
        assert result.connection_id == "existing_conn"
        mock_storage.update_connection_tokens.assert_called_once()
        mock_storage.create_connection.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_callback_invalid_state(self, oauth_manager):
        """Test callback with invalid state fails."""
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.validate_and_consume.side_effect = AuthError(
            message="Invalid state",
            code="invalid_state",
        )

        result = await oauth_manager.handle_callback(code="auth_code", state="invalid_state")

        assert result.success is False
        assert "Invalid state" in result.error

    @pytest.mark.asyncio
    async def test_handle_callback_exchange_error(self, oauth_manager):
        """Test callback when code exchange fails."""
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.validate_and_consume.return_value = OAuthState(
            id="state_id_error",
            state="test_state",
            user_id="user_123",
            code_verifier="verifier",
            scopes=[],
            redirect_uri="http://localhost:8000/callback",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            created_at=datetime.utcnow(),
        )

        oauth_manager._google_client = AsyncMock()
        oauth_manager._google_client.exchange_code.side_effect = Exception("Exchange failed")

        result = await oauth_manager.handle_callback(code="bad_code", state="test_state")

        assert result.success is False
        assert "Exchange failed" in result.error


class TestDisconnect:
    """Tests for disconnect."""

    @pytest.mark.asyncio
    async def test_disconnect_with_revoke(self, oauth_manager, mock_storage, mock_encryption):
        """Test disconnecting with Google revocation."""
        connection = Connection(
            id="conn_123",
            user_id="user_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted_access",
            refresh_token_encrypted="encrypted_refresh",
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_connection.return_value = connection

        oauth_manager._google_client = AsyncMock()

        result = await oauth_manager.disconnect("conn_123", revoke_google_access=True)

        assert result is True
        oauth_manager._google_client.revoke_token.assert_called_once()
        mock_storage.deactivate_connection.assert_called_once_with("conn_123")

    @pytest.mark.asyncio
    async def test_disconnect_without_revoke(self, oauth_manager, mock_storage):
        """Test disconnecting without Google revocation."""
        connection = Connection(
            id="conn_123",
            user_id="user_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow(),
            scopes=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_connection.return_value = connection

        oauth_manager._google_client = AsyncMock()

        result = await oauth_manager.disconnect("conn_123", revoke_google_access=False)

        assert result is True
        oauth_manager._google_client.revoke_token.assert_not_called()
        mock_storage.deactivate_connection.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self, oauth_manager, mock_storage):
        """Test disconnecting non-existent connection."""
        mock_storage.get_connection.return_value = None

        result = await oauth_manager.disconnect("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_revoke_fails_continues(self, oauth_manager, mock_storage, mock_encryption):
        """Test disconnecting continues if revoke fails."""
        connection = Connection(
            id="conn_123",
            user_id="user_123",
            gmail_address="user@gmail.com",
            access_token_encrypted="encrypted",
            refresh_token_encrypted="encrypted",
            token_expires_at=datetime.utcnow(),
            scopes=[],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_used_at=None,
        )
        mock_storage.get_connection.return_value = connection

        oauth_manager._google_client = AsyncMock()
        oauth_manager._google_client.revoke_token.side_effect = Exception("Revoke failed")

        result = await oauth_manager.disconnect("conn_123", revoke_google_access=True)

        # Should still succeed even if revoke fails
        assert result is True
        mock_storage.deactivate_connection.assert_called_once()


class TestCleanupExpiredStates:
    """Tests for cleanup_expired_states."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_states(self, oauth_manager):
        """Test cleaning up expired states."""
        oauth_manager._state_manager = AsyncMock()
        oauth_manager._state_manager.cleanup_expired.return_value = 5

        count = await oauth_manager.cleanup_expired_states()

        assert count == 5
        oauth_manager._state_manager.cleanup_expired.assert_called_once()


class TestClose:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    async def test_close(self, oauth_manager):
        """Test closing resources."""
        oauth_manager._google_client = AsyncMock()

        await oauth_manager.close()

        oauth_manager._google_client.close.assert_called_once()
