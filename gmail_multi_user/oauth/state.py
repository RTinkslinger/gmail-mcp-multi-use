"""OAuth state management for CSRF protection.

This module manages OAuth state parameters used to prevent
Cross-Site Request Forgery (CSRF) attacks during the OAuth flow.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from gmail_multi_user.exceptions import AuthError
from gmail_multi_user.oauth.pkce import PKCE
from gmail_multi_user.types import OAuthState

if TYPE_CHECKING:
    from gmail_multi_user.storage.base import StorageBackend


class OAuthStateManager:
    """Manages OAuth state for CSRF protection.

    OAuth state parameters are:
    - Cryptographically random (32 bytes)
    - Stored in the database with associated PKCE verifier
    - Expired after a configurable TTL (default 10 minutes)
    - Single-use (deleted after successful validation)

    Example:
        manager = OAuthStateManager(storage, ttl_seconds=600)
        state = await manager.create_state(user_id, scopes, redirect_uri)
        # ... user completes OAuth ...
        oauth_state = await manager.validate_and_consume(state_string)
    """

    DEFAULT_TTL_SECONDS = 600  # 10 minutes
    STATE_BYTES = 32  # 256 bits of entropy

    def __init__(
        self,
        storage: StorageBackend,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        """Initialize the state manager.

        Args:
            storage: Storage backend for persisting states.
            ttl_seconds: Time-to-live for states in seconds.
        """
        self._storage = storage
        self._ttl_seconds = ttl_seconds

    async def create_state(
        self,
        user_id: str,
        scopes: list[str],
        redirect_uri: str,
    ) -> OAuthState:
        """Create a new OAuth state with PKCE.

        Args:
            user_id: Internal user ID initiating the OAuth flow.
            scopes: OAuth scopes being requested.
            redirect_uri: Redirect URI for the callback.

        Returns:
            OAuthState object with state string and PKCE verifier.
        """
        # Generate cryptographically random state
        state_string = self._generate_state()

        # Generate PKCE code verifier
        pkce = PKCE.generate()

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(seconds=self._ttl_seconds)

        # Store in database
        oauth_state = await self._storage.create_oauth_state(
            state=state_string,
            user_id=user_id,
            scopes=scopes,
            redirect_uri=redirect_uri,
            code_verifier=pkce.code_verifier,
            expires_at=expires_at,
        )

        return oauth_state

    async def validate_state(self, state: str) -> OAuthState | None:
        """Validate a state parameter without consuming it.

        Args:
            state: The state string to validate.

        Returns:
            OAuthState if valid and not expired, None otherwise.
        """
        oauth_state = await self._storage.get_oauth_state(state)

        if oauth_state is None:
            return None

        if oauth_state.is_expired:
            # Clean up expired state
            await self._storage.delete_oauth_state(state)
            return None

        return oauth_state

    async def validate_and_consume(self, state: str) -> OAuthState:
        """Validate and consume a state parameter (single-use).

        Args:
            state: The state string to validate and consume.

        Returns:
            OAuthState if valid.

        Raises:
            AuthError: If state is invalid or expired.
        """
        oauth_state = await self._storage.get_oauth_state(state)

        if oauth_state is None:
            raise AuthError(
                message="Invalid OAuth state parameter",
                code="invalid_state",
            )

        if oauth_state.is_expired:
            # Clean up expired state
            await self._storage.delete_oauth_state(state)
            raise AuthError(
                message="OAuth state has expired. Please restart the authorization flow.",
                code="state_expired",
                details={"expired_at": oauth_state.expires_at.isoformat()},
            )

        # Delete the state (single-use)
        await self._storage.delete_oauth_state(state)

        return oauth_state

    async def cleanup_expired(self) -> int:
        """Remove all expired OAuth states.

        Returns:
            Number of expired states deleted.
        """
        return await self._storage.cleanup_expired_states()

    @classmethod
    def _generate_state(cls) -> str:
        """Generate a cryptographically random state string.

        Returns:
            URL-safe random string (32 bytes = 43 characters).
        """
        return secrets.token_urlsafe(cls.STATE_BYTES)

    def get_pkce_challenge(self, code_verifier: str) -> str:
        """Get the PKCE code challenge for a verifier.

        Args:
            code_verifier: The PKCE code verifier.

        Returns:
            The corresponding code challenge.
        """
        pkce = PKCE(code_verifier)
        return pkce.code_challenge
