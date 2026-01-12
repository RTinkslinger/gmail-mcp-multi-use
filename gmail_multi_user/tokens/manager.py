"""Token management for automatic refresh and validation.

This module handles token lifecycle management including:
- Automatic refresh before expiration
- Decryption for API use
- Re-authentication detection
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from gmail_multi_user.exceptions import (
    ConnectionInactiveError,
    ConnectionNotFoundError,
    TokenError,
)
from gmail_multi_user.logging import LogContext, get_logger
from gmail_multi_user.oauth.google import GoogleOAuthClient

logger = get_logger(__name__)

if TYPE_CHECKING:
    from gmail_multi_user.config import Config
    from gmail_multi_user.storage.base import StorageBackend
    from gmail_multi_user.tokens.encryption import TokenEncryption
    from gmail_multi_user.types import Connection


@dataclass
class ValidToken:
    """A validated and decrypted access token ready for use."""

    access_token: str
    expires_at: datetime
    connection_id: str
    gmail_address: str


class TokenManager:
    """Manages token validation, decryption, and automatic refresh.

    This class ensures API calls always have a valid access token by:
    1. Checking token expiration with a configurable buffer
    2. Automatically refreshing tokens before they expire
    3. Handling refresh failures by marking connections for re-auth

    Example:
        manager = TokenManager(config, storage, encryption)

        # Get a valid token for an API call
        token = await manager.get_valid_token(connection_id)
        # Use token.access_token for Gmail API

        # Token is automatically refreshed if expiring soon
    """

    def __init__(
        self,
        config: Config,
        storage: StorageBackend,
        encryption: TokenEncryption,
    ) -> None:
        """Initialize the token manager.

        Args:
            config: Application configuration.
            storage: Storage backend.
            encryption: Token encryption utility.
        """
        self._config = config
        self._storage = storage
        self._encryption = encryption
        self._refresh_buffer = timedelta(seconds=config.token_refresh_buffer_seconds)
        self._google_client = GoogleOAuthClient(config.google)

    async def close(self) -> None:
        """Close resources."""
        await self._google_client.close()

    async def get_valid_token(self, connection_id: str) -> ValidToken:
        """Get a valid access token for a connection.

        This method:
        1. Retrieves the connection from storage
        2. Checks if the token needs refreshing
        3. Refreshes if necessary
        4. Returns a decrypted, valid token

        Args:
            connection_id: The connection to get a token for.

        Returns:
            ValidToken with decrypted access token.

        Raises:
            ConnectionNotFoundError: If connection doesn't exist.
            ConnectionInactiveError: If connection is inactive.
            TokenError: If token refresh fails.
        """
        connection = await self._storage.get_connection(connection_id)

        if connection is None:
            raise ConnectionNotFoundError(
                message=f"Connection not found: {connection_id}",
                details={"connection_id": connection_id},
            )

        if not connection.is_active:
            raise ConnectionInactiveError(
                message=f"Connection is inactive: {connection_id}",
                details={
                    "connection_id": connection_id,
                    "gmail_address": connection.gmail_address,
                },
            )

        # Check if token needs refresh
        if self._needs_refresh(connection):
            connection = await self._refresh_token(connection)

        # Decrypt and return token
        access_token = self._encryption.decrypt(connection.access_token_encrypted)

        # Update last used timestamp
        await self._storage.update_connection_last_used(connection_id)

        return ValidToken(
            access_token=access_token,
            expires_at=connection.token_expires_at,
            connection_id=connection.id,
            gmail_address=connection.gmail_address,
        )

    async def refresh_token(self, connection_id: str) -> ValidToken:
        """Force refresh a token.

        Args:
            connection_id: The connection to refresh.

        Returns:
            ValidToken with new access token.

        Raises:
            ConnectionNotFoundError: If connection doesn't exist.
            TokenError: If refresh fails.
        """
        connection = await self._storage.get_connection(connection_id)

        if connection is None:
            raise ConnectionNotFoundError(
                message=f"Connection not found: {connection_id}",
                details={"connection_id": connection_id},
            )

        connection = await self._refresh_token(connection)

        access_token = self._encryption.decrypt(connection.access_token_encrypted)

        return ValidToken(
            access_token=access_token,
            expires_at=connection.token_expires_at,
            connection_id=connection.id,
            gmail_address=connection.gmail_address,
        )

    async def refresh_expiring_tokens(self) -> list[str]:
        """Refresh all tokens that are expiring soon.

        This method is useful for background token refresh jobs.

        Returns:
            List of connection IDs that were refreshed.
        """
        expires_before = datetime.utcnow() + self._refresh_buffer
        expiring = await self._storage.get_expiring_connections(expires_before)

        refreshed = []
        for connection in expiring:
            try:
                await self._refresh_token(connection)
                refreshed.append(connection.id)
            except TokenError:
                # Mark as needing re-auth
                await self._storage.deactivate_connection(connection.id)

        return refreshed

    def _needs_refresh(self, connection: Connection) -> bool:
        """Check if a token needs to be refreshed.

        Args:
            connection: The connection to check.

        Returns:
            True if token expires within the refresh buffer.
        """
        return datetime.utcnow() + self._refresh_buffer >= connection.token_expires_at

    async def _refresh_token(self, connection: Connection) -> Connection:
        """Refresh a connection's access token.

        Args:
            connection: The connection to refresh.

        Returns:
            Updated connection with new token.

        Raises:
            TokenError: If refresh fails.
        """
        with LogContext(connection_id=connection.id, operation="token_refresh"):
            logger.info("Refreshing access token")

            # Decrypt refresh token
            try:
                refresh_token = self._encryption.decrypt(
                    connection.refresh_token_encrypted
                )
            except Exception as e:
                logger.error("Failed to decrypt refresh token", error=str(e))
                raise TokenError(
                    message="Failed to decrypt refresh token",
                    code="encryption_error",
                    details={"connection_id": connection.id},
                ) from e

            if not refresh_token:
                logger.warning("No refresh token available")
                raise TokenError(
                    message="No refresh token available",
                    code="needs_reauth",
                    details={"connection_id": connection.id},
                )

            try:
                # Call Google to refresh
                token_response = await self._google_client.refresh_access_token(
                    refresh_token
                )

                # Encrypt new tokens
                access_token_encrypted = self._encryption.encrypt(
                    token_response.access_token
                )

                # Only update refresh token if a new one was provided
                refresh_token_encrypted = None
                if token_response.refresh_token:
                    refresh_token_encrypted = self._encryption.encrypt(
                        token_response.refresh_token
                    )

                # Update in storage
                updated = await self._storage.update_connection_tokens(
                    connection_id=connection.id,
                    access_token_encrypted=access_token_encrypted,
                    refresh_token_encrypted=refresh_token_encrypted,
                    token_expires_at=token_response.expires_at,
                )

                logger.info("Token refreshed successfully", expires_at=str(token_response.expires_at))
                return updated

            except TokenError:
                # Re-raise TokenError (e.g., token_revoked)
                logger.warning("Token refresh failed with TokenError")
                raise
            except Exception as e:
                logger.error("Token refresh failed", error=str(e))
                raise TokenError(
                    message=f"Token refresh failed: {e}",
                    code="refresh_failed",
                    details={"connection_id": connection.id},
                ) from e

    async def check_connection_valid(self, connection_id: str) -> bool:
        """Check if a connection is valid and has working tokens.

        Args:
            connection_id: The connection to check.

        Returns:
            True if connection is valid and tokens work.
        """
        try:
            await self.get_valid_token(connection_id)
            return True
        except (ConnectionNotFoundError, ConnectionInactiveError, TokenError):
            return False
