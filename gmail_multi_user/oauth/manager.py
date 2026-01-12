"""OAuth flow manager.

This module orchestrates the complete OAuth 2.0 authorization flow,
coordinating state management, PKCE, Google API calls, and token storage.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from gmail_multi_user.exceptions import AuthError
from gmail_multi_user.logging import LogContext, get_logger
from gmail_multi_user.oauth.google import GoogleOAuthClient
from gmail_multi_user.oauth.state import OAuthStateManager
from gmail_multi_user.types import AuthUrlResult, CallbackResult

logger = get_logger(__name__)

if TYPE_CHECKING:
    from gmail_multi_user.config import Config
    from gmail_multi_user.storage.base import StorageBackend
    from gmail_multi_user.tokens.encryption import TokenEncryption


class OAuthManager:
    """Manages the complete OAuth 2.0 authorization flow.

    This class coordinates:
    - Authorization URL generation with PKCE
    - State management for CSRF protection
    - Token exchange with Google
    - Token encryption and storage
    - Connection creation

    Example:
        manager = OAuthManager(config, storage, encryption)

        # Step 1: Generate auth URL
        result = await manager.get_auth_url(user_id="user_123")
        # Redirect user to result.auth_url

        # Step 2: Handle callback (after user authorizes)
        callback_result = await manager.handle_callback(code, state)
        if callback_result.success:
            print(f"Connected: {callback_result.gmail_address}")
    """

    def __init__(
        self,
        config: Config,
        storage: StorageBackend,
        encryption: TokenEncryption,
    ) -> None:
        """Initialize the OAuth manager.

        Args:
            config: Application configuration.
            storage: Storage backend for persisting data.
            encryption: Token encryption utility.
        """
        self._config = config
        self._storage = storage
        self._encryption = encryption
        self._state_manager = OAuthStateManager(
            storage,
            ttl_seconds=config.oauth_state_ttl_seconds,
        )
        self._google_client = GoogleOAuthClient(config.google)

    async def close(self) -> None:
        """Close resources."""
        await self._google_client.close()

    async def get_auth_url(
        self,
        user_id: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> AuthUrlResult:
        """Generate an OAuth authorization URL for a user.

        Args:
            user_id: External user identifier from your application.
            scopes: OAuth scopes to request (defaults to config scopes).
            redirect_uri: Override the configured redirect URI.

        Returns:
            AuthUrlResult with the authorization URL and state.
        """
        with LogContext(user_id=user_id, operation="get_auth_url"):
            logger.info("Generating OAuth authorization URL", scope_count=len(scopes) if scopes else 0)

            # Ensure user exists
            user = await self._storage.get_or_create_user(external_user_id=user_id)

            # Use default scopes if not specified
            if scopes is None:
                scopes = list(self._config.google.scopes)

            # Use default redirect if not specified
            if redirect_uri is None:
                redirect_uri = self._config.google.redirect_uri

            # Create OAuth state with PKCE
            oauth_state = await self._state_manager.create_state(
                user_id=user.id,
                scopes=scopes,
                redirect_uri=redirect_uri,
            )

            # Get PKCE challenge from stored verifier
            code_challenge = self._state_manager.get_pkce_challenge(
                oauth_state.code_verifier
            )

            # Build the authorization URL
            auth_url = self._google_client.build_auth_url(
                state=oauth_state.state,
                code_challenge=code_challenge,
                scopes=scopes,
                redirect_uri=redirect_uri,
            )

            logger.debug("OAuth URL generated", state=oauth_state.state[:8] + "...")

            return AuthUrlResult(
                auth_url=auth_url,
                state=oauth_state.state,
                expires_at=oauth_state.expires_at,
            )

    async def handle_callback(
        self,
        code: str,
        state: str,
    ) -> CallbackResult:
        """Handle the OAuth callback after user authorization.

        Args:
            code: Authorization code from Google.
            state: State parameter for CSRF validation.

        Returns:
            CallbackResult with success status and connection details.
        """
        with LogContext(operation="oauth_callback"):
            logger.info("Processing OAuth callback", state=state[:8] + "...")
            try:
                # Validate and consume state (single-use)
                oauth_state = await self._state_manager.validate_and_consume(state)

                # Exchange code for tokens
                token_response = await self._google_client.exchange_code(
                    code=code,
                    code_verifier=oauth_state.code_verifier,
                    redirect_uri=oauth_state.redirect_uri,
                )

                # Get user email from Google
                user_info = await self._google_client.get_user_info(
                    token_response.access_token
                )

                logger.debug("User info retrieved", email=user_info.email)

                # Encrypt tokens
                access_token_encrypted = self._encryption.encrypt(
                    token_response.access_token
                )
                refresh_token_encrypted = self._encryption.encrypt(
                    token_response.refresh_token or ""
                )

                # Check if connection already exists
                existing = await self._storage.get_connection_by_user_and_email(
                    user_id=oauth_state.user_id,
                    gmail_address=user_info.email,
                )

                if existing:
                    # Update existing connection with new tokens
                    connection = await self._storage.update_connection_tokens(
                        connection_id=existing.id,
                        access_token_encrypted=access_token_encrypted,
                        refresh_token_encrypted=refresh_token_encrypted,
                        token_expires_at=token_response.expires_at,
                    )
                    logger.info("Updated existing connection", connection_id=connection.id)
                    # Note: If connection was deactivated, updating tokens doesn't
                    # reactivate it. The user would need to explicitly reactivate
                    # or we could add a reactivate method. For now, tokens are updated.
                else:
                    # Create new connection
                    connection = await self._storage.create_connection(
                        user_id=oauth_state.user_id,
                        gmail_address=user_info.email,
                        access_token_encrypted=access_token_encrypted,
                        refresh_token_encrypted=refresh_token_encrypted,
                        token_expires_at=token_response.expires_at,
                        scopes=oauth_state.scopes,
                    )
                    logger.info("Created new connection", connection_id=connection.id)

                # Get the user's external ID for the response
                user = await self._storage.get_user_by_id(oauth_state.user_id)

                return CallbackResult(
                    success=True,
                    connection_id=connection.id,
                    user_id=user.external_user_id if user else None,
                    gmail_address=user_info.email,
                )

            except AuthError as e:
                logger.warning("OAuth callback failed", error=e.message, code=e.code)
                return CallbackResult(
                    success=False,
                    error=e.message,
                )
            except Exception as e:
                logger.error("OAuth callback error", error=str(e), exc_info=True)
                return CallbackResult(
                    success=False,
                    error=str(e),
                )

    async def disconnect(
        self,
        connection_id: str,
        revoke_google_access: bool = True,
    ) -> bool:
        """Disconnect a Gmail account.

        Args:
            connection_id: The connection to disconnect.
            revoke_google_access: Also revoke access at Google.

        Returns:
            True if disconnected successfully.
        """
        with LogContext(connection_id=connection_id, operation="disconnect"):
            logger.info("Disconnecting Gmail account", revoke_google_access=revoke_google_access)

            connection = await self._storage.get_connection(connection_id)
            if not connection:
                logger.warning("Connection not found for disconnect")
                return False

            # Optionally revoke at Google
            if revoke_google_access:
                try:
                    # Decrypt refresh token and revoke
                    refresh_token = self._encryption.decrypt(
                        connection.refresh_token_encrypted
                    )
                    await self._google_client.revoke_token(refresh_token)
                    logger.debug("Google access revoked")
                except Exception as e:
                    # Continue even if revocation fails
                    logger.warning("Google revocation failed", error=str(e))

            # Deactivate the connection
            await self._storage.deactivate_connection(connection_id)
            logger.info("Connection disconnected")

            return True

    async def cleanup_expired_states(self) -> int:
        """Clean up expired OAuth states.

        Returns:
            Number of expired states deleted.
        """
        return await self._state_manager.cleanup_expired()
