"""Abstract storage backend interface.

This module defines the StorageBackend protocol that all storage
implementations must follow.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from gmail_multi_user.types import Connection, OAuthState, User


class StorageBackend(ABC):
    """Abstract base class for storage backends.

    All storage implementations (SQLite, Supabase) must implement this interface.
    Methods are async to support both sync (via asyncio.run) and async usage.
    """

    # =========================================================================
    # Lifecycle Methods
    # =========================================================================

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend.

        This should create tables if they don't exist and run any pending
        migrations.
        """

    @abstractmethod
    async def close(self) -> None:
        """Close the storage backend and release resources."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the storage backend is healthy and connected.

        Returns:
            True if healthy, False otherwise.
        """

    # =========================================================================
    # User Methods
    # =========================================================================

    @abstractmethod
    async def get_or_create_user(
        self,
        external_user_id: str,
        email: str | None = None,
    ) -> User:
        """Get an existing user or create a new one.

        Args:
            external_user_id: The developer's user identifier.
            email: Optional email for debugging purposes.

        Returns:
            The User object.
        """

    @abstractmethod
    async def get_user_by_external_id(self, external_user_id: str) -> User | None:
        """Get a user by their external ID.

        Args:
            external_user_id: The developer's user identifier.

        Returns:
            The User object, or None if not found.
        """

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get a user by their internal ID.

        Args:
            user_id: The internal user ID.

        Returns:
            The User object, or None if not found.
        """

    @abstractmethod
    async def list_users(self) -> list[User]:
        """List all users.

        Returns:
            List of all User objects.
        """

    # =========================================================================
    # Connection Methods
    # =========================================================================

    @abstractmethod
    async def create_connection(
        self,
        user_id: str,
        gmail_address: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str,
        token_expires_at: datetime,
        scopes: list[str],
    ) -> Connection:
        """Create a new Gmail connection.

        Args:
            user_id: The internal user ID.
            gmail_address: The Gmail email address.
            access_token_encrypted: Encrypted access token.
            refresh_token_encrypted: Encrypted refresh token.
            token_expires_at: When the access token expires.
            scopes: List of granted OAuth scopes.

        Returns:
            The created Connection object.
        """

    @abstractmethod
    async def get_connection(self, connection_id: str) -> Connection | None:
        """Get a connection by ID.

        Args:
            connection_id: The connection ID.

        Returns:
            The Connection object, or None if not found.
        """

    @abstractmethod
    async def get_connection_by_user_and_email(
        self,
        user_id: str,
        gmail_address: str,
    ) -> Connection | None:
        """Get a connection by user ID and Gmail address.

        Args:
            user_id: The internal user ID.
            gmail_address: The Gmail email address.

        Returns:
            The Connection object, or None if not found.
        """

    @abstractmethod
    async def list_connections(
        self,
        user_id: str | None = None,
        include_inactive: bool = False,
    ) -> list[Connection]:
        """List connections, optionally filtered by user.

        Args:
            user_id: Filter by user ID (None for all users).
            include_inactive: Include inactive/revoked connections.

        Returns:
            List of Connection objects.
        """

    @abstractmethod
    async def update_connection_tokens(
        self,
        connection_id: str,
        access_token_encrypted: str,
        refresh_token_encrypted: str | None,
        token_expires_at: datetime,
    ) -> Connection:
        """Update a connection's tokens after refresh.

        Args:
            connection_id: The connection ID.
            access_token_encrypted: New encrypted access token.
            refresh_token_encrypted: New encrypted refresh token (optional).
            token_expires_at: New expiration time.

        Returns:
            The updated Connection object.
        """

    @abstractmethod
    async def update_connection_last_used(self, connection_id: str) -> None:
        """Update a connection's last_used_at timestamp.

        Args:
            connection_id: The connection ID.
        """

    @abstractmethod
    async def deactivate_connection(self, connection_id: str) -> None:
        """Mark a connection as inactive.

        Args:
            connection_id: The connection ID.
        """

    @abstractmethod
    async def delete_connection(self, connection_id: str) -> None:
        """Permanently delete a connection.

        Args:
            connection_id: The connection ID.
        """

    @abstractmethod
    async def get_expiring_connections(
        self,
        expires_before: datetime,
    ) -> list[Connection]:
        """Get connections with tokens expiring before a given time.

        Args:
            expires_before: Return connections expiring before this time.

        Returns:
            List of Connection objects with expiring tokens.
        """

    # =========================================================================
    # OAuth State Methods
    # =========================================================================

    @abstractmethod
    async def create_oauth_state(
        self,
        state: str,
        user_id: str,
        scopes: list[str],
        redirect_uri: str,
        code_verifier: str,
        expires_at: datetime,
    ) -> OAuthState:
        """Create a new OAuth state for CSRF protection.

        Args:
            state: The OAuth state string.
            user_id: The user initiating the OAuth flow.
            scopes: Requested OAuth scopes.
            redirect_uri: The OAuth redirect URI.
            code_verifier: PKCE code verifier.
            expires_at: When the state expires.

        Returns:
            The created OAuthState object.
        """

    @abstractmethod
    async def get_oauth_state(self, state: str) -> OAuthState | None:
        """Get an OAuth state by state string.

        Args:
            state: The OAuth state string.

        Returns:
            The OAuthState object, or None if not found.
        """

    @abstractmethod
    async def delete_oauth_state(self, state: str) -> None:
        """Delete an OAuth state after use.

        Args:
            state: The OAuth state string.
        """

    @abstractmethod
    async def cleanup_expired_states(self) -> int:
        """Delete all expired OAuth states.

        Returns:
            Number of states deleted.
        """
