"""Tests for token management."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gmail_multi_user.exceptions import (
    ConnectionInactiveError,
    ConnectionNotFoundError,
    TokenError,
)
from gmail_multi_user.oauth.google import GoogleOAuthClient
from gmail_multi_user.tokens.manager import TokenManager


class TestGoogleOAuthClient:
    """Tests for Google OAuth client."""

    @pytest.fixture
    def google_client(self, google_oauth_config) -> GoogleOAuthClient:
        """Create a Google OAuth client."""
        return GoogleOAuthClient(google_oauth_config)

    def test_build_auth_url(self, google_client: GoogleOAuthClient) -> None:
        """Test building authorization URL."""
        url = google_client.build_auth_url(
            state="test_state",
            code_challenge="test_challenge",
        )

        assert "accounts.google.com" in url
        assert "state=test_state" in url
        assert "code_challenge=test_challenge" in url
        assert "code_challenge_method=S256" in url
        assert "response_type=code" in url
        assert "access_type=offline" in url

    def test_build_auth_url_with_custom_scopes(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test building auth URL with custom scopes."""
        url = google_client.build_auth_url(
            state="test_state",
            code_challenge="test_challenge",
            scopes=["gmail.send", "gmail.modify"],
        )

        assert "gmail.send" in url
        assert "gmail.modify" in url

    def test_build_auth_url_with_custom_redirect(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test building auth URL with custom redirect."""
        url = google_client.build_auth_url(
            state="test_state",
            code_challenge="test_challenge",
            redirect_uri="http://custom:9000/callback",
        )

        assert "http%3A%2F%2Fcustom%3A9000%2Fcallback" in url

    @pytest.mark.asyncio
    async def test_exchange_code_success(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test successful code exchange."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "gmail.readonly",
        }

        with patch.object(
            google_client,
            "_get_client",
            return_value=AsyncMock(post=AsyncMock(return_value=mock_response)),
        ):
            result = await google_client.exchange_code(
                code="test_code",
                code_verifier="test_verifier",
            )

        assert result.access_token == "test_access_token"
        assert result.refresh_token == "test_refresh_token"
        assert result.token_type == "Bearer"

    @pytest.mark.asyncio
    async def test_exchange_code_failure(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test code exchange failure."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": "invalid_grant"}'
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Code expired",
        }

        with patch.object(
            google_client,
            "_get_client",
            return_value=AsyncMock(post=AsyncMock(return_value=mock_response)),
        ):
            from gmail_multi_user.exceptions import AuthError

            with pytest.raises(AuthError) as exc_info:
                await google_client.exchange_code(
                    code="test_code",
                    code_verifier="test_verifier",
                )

            assert exc_info.value.code == "oauth_failed"

    @pytest.mark.asyncio
    async def test_refresh_access_token_success(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test successful token refresh."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }

        with patch.object(
            google_client,
            "_get_client",
            return_value=AsyncMock(post=AsyncMock(return_value=mock_response)),
        ):
            result = await google_client.refresh_access_token("test_refresh_token")

        assert result.access_token == "new_access_token"
        assert result.refresh_token is None  # Not returned on refresh

    @pytest.mark.asyncio
    async def test_refresh_token_revoked(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test refresh with revoked token."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = b'{"error": "invalid_grant"}'
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "Token has been revoked",
        }

        with patch.object(
            google_client,
            "_get_client",
            return_value=AsyncMock(post=AsyncMock(return_value=mock_response)),
        ):
            with pytest.raises(TokenError) as exc_info:
                await google_client.refresh_access_token("revoked_token")

            assert exc_info.value.code == "token_revoked"

    @pytest.mark.asyncio
    async def test_get_user_info_success(
        self,
        google_client: GoogleOAuthClient,
    ) -> None:
        """Test getting user info."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "email": "user@gmail.com",
            "verified_email": True,
            "name": "Test User",
        }

        with patch.object(
            google_client,
            "_get_client",
            return_value=AsyncMock(get=AsyncMock(return_value=mock_response)),
        ):
            result = await google_client.get_user_info("test_access_token")

        assert result.email == "user@gmail.com"
        assert result.verified_email is True
        assert result.name == "Test User"


class TestTokenManager:
    """Tests for token manager."""

    @pytest.fixture
    def token_manager(
        self,
        test_config,
        sqlite_backend,
        token_encryptor,
    ) -> TokenManager:
        """Create a token manager."""
        return TokenManager(test_config, sqlite_backend, token_encryptor)

    @pytest.mark.asyncio
    async def test_get_valid_token_not_found(
        self,
        token_manager: TokenManager,
    ) -> None:
        """Test getting token for non-existent connection."""
        with pytest.raises(ConnectionNotFoundError):
            await token_manager.get_valid_token("nonexistent_id")

    @pytest.mark.asyncio
    async def test_get_valid_token_inactive(
        self,
        token_manager: TokenManager,
        sqlite_backend_with_user: tuple,
        test_connection_data: dict,
    ) -> None:
        """Test getting token for inactive connection."""
        backend, user_id = sqlite_backend_with_user

        # Create connection
        connection = await backend.create_connection(
            user_id=user_id,
            **test_connection_data,
        )

        # Deactivate it
        await backend.deactivate_connection(connection.id)

        # Create new manager with the same backend
        manager = TokenManager(
            token_manager._config,
            backend,
            token_manager._encryption,
        )

        with pytest.raises(ConnectionInactiveError):
            await manager.get_valid_token(connection.id)

    @pytest.mark.asyncio
    async def test_get_valid_token_no_refresh_needed(
        self,
        test_config,
        sqlite_backend_with_user: tuple,
        token_encryptor,
    ) -> None:
        """Test getting valid token that doesn't need refresh."""
        backend, user_id = sqlite_backend_with_user

        # Create connection with token expiring in 1 hour (no refresh needed)
        connection = await backend.create_connection(
            user_id=user_id,
            gmail_address="test@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("valid_access_token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh_token"),
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        manager = TokenManager(test_config, backend, token_encryptor)

        token = await manager.get_valid_token(connection.id)

        assert token.access_token == "valid_access_token"
        assert token.connection_id == connection.id
        assert token.gmail_address == "test@gmail.com"

    @pytest.mark.asyncio
    async def test_needs_refresh_within_buffer(
        self,
        test_config,
        sqlite_backend_with_user: tuple,
        token_encryptor,
    ) -> None:
        """Test that token expiring within buffer needs refresh."""
        backend, user_id = sqlite_backend_with_user

        # Create connection with token expiring in 2 minutes (within 5-min buffer)
        connection = await backend.create_connection(
            user_id=user_id,
            gmail_address="test@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("expiring_token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh_token"),
            token_expires_at=datetime.utcnow() + timedelta(minutes=2),
            scopes=["gmail.readonly"],
        )

        manager = TokenManager(test_config, backend, token_encryptor)

        # Check that _needs_refresh returns True
        conn = await backend.get_connection(connection.id)
        assert manager._needs_refresh(conn) is True

    @pytest.mark.asyncio
    async def test_check_connection_valid(
        self,
        test_config,
        sqlite_backend_with_user: tuple,
        token_encryptor,
    ) -> None:
        """Test checking connection validity."""
        backend, user_id = sqlite_backend_with_user

        connection = await backend.create_connection(
            user_id=user_id,
            gmail_address="test@gmail.com",
            access_token_encrypted=token_encryptor.encrypt("valid_token"),
            refresh_token_encrypted=token_encryptor.encrypt("refresh_token"),
            token_expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["gmail.readonly"],
        )

        manager = TokenManager(test_config, backend, token_encryptor)

        is_valid = await manager.check_connection_valid(connection.id)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_check_connection_invalid(
        self,
        test_config,
        sqlite_backend_with_user: tuple,
        token_encryptor,
    ) -> None:
        """Test checking invalid connection."""
        backend, user_id = sqlite_backend_with_user

        manager = TokenManager(test_config, backend, token_encryptor)

        is_valid = await manager.check_connection_valid("nonexistent")
        assert is_valid is False
