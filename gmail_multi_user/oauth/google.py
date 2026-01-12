"""Google OAuth 2.0 client.

This module handles HTTP communication with Google OAuth endpoints
for token exchange, refresh, and user info retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import httpx

from gmail_multi_user.exceptions import AuthError, TokenError

if TYPE_CHECKING:
    from gmail_multi_user.config import GoogleOAuthConfig


# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


@dataclass
class TokenResponse:
    """Response from Google token endpoint."""

    access_token: str
    refresh_token: str | None
    expires_at: datetime
    token_type: str
    scope: str


@dataclass
class UserInfo:
    """User info from Google userinfo endpoint."""

    email: str
    verified_email: bool
    name: str | None = None
    picture: str | None = None


class GoogleOAuthClient:
    """Client for Google OAuth 2.0 operations.

    Handles:
    - Building authorization URLs
    - Exchanging authorization codes for tokens
    - Refreshing access tokens
    - Fetching user information
    - Revoking tokens

    Example:
        client = GoogleOAuthClient(config)
        tokens = await client.exchange_code(code, verifier, redirect_uri)
        user_info = await client.get_user_info(tokens.access_token)
    """

    def __init__(
        self,
        config: GoogleOAuthConfig,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the Google OAuth client.

        Args:
            config: Google OAuth configuration.
            http_client: Optional httpx client for testing.
        """
        self._config = config
        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def build_auth_url(
        self,
        state: str,
        code_challenge: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> str:
        """Build the Google OAuth authorization URL.

        Args:
            state: OAuth state parameter for CSRF protection.
            code_challenge: PKCE code challenge.
            scopes: OAuth scopes to request (defaults to config scopes).
            redirect_uri: Redirect URI (defaults to config redirect_uri).

        Returns:
            Complete authorization URL to redirect user to.
        """
        params = {
            "client_id": self._config.client_id,
            "redirect_uri": redirect_uri or self._config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes or self._config.scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Always show consent screen for refresh token
        }

        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str | None = None,
    ) -> TokenResponse:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.
            code_verifier: PKCE code verifier.
            redirect_uri: Redirect URI used in authorization.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            AuthError: If token exchange fails.
        """
        client = await self._get_client()

        data = {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri or self._config.redirect_uri,
        }

        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.RequestError as e:
            raise AuthError(
                message=f"Failed to connect to Google OAuth: {e}",
                code="oauth_failed",
                details={"error": str(e)},
            ) from e

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            raise AuthError(
                message=f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}",
                code="oauth_failed",
                details={
                    "status_code": response.status_code,
                    "error": error_data.get("error"),
                    "error_description": error_data.get("error_description"),
                },
            )

        return self._parse_token_response(response.json())

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an access token.

        Args:
            refresh_token: The refresh token.

        Returns:
            TokenResponse with new access token.

        Raises:
            TokenError: If refresh fails.
        """
        client = await self._get_client()

        data = {
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.RequestError as e:
            raise TokenError(
                message=f"Failed to connect to Google OAuth: {e}",
                code="refresh_failed",
                details={"error": str(e)},
            ) from e

        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error = error_data.get("error", "")

            # Check if token was revoked
            if error == "invalid_grant":
                raise TokenError(
                    message="Refresh token is invalid or revoked. User must re-authenticate.",
                    code="token_revoked",
                    details=error_data,
                )

            raise TokenError(
                message=f"Token refresh failed: {error_data.get('error_description', 'Unknown error')}",
                code="refresh_failed",
                details={
                    "status_code": response.status_code,
                    "error": error,
                    "error_description": error_data.get("error_description"),
                },
            )

        # Note: refresh response may not include a new refresh_token
        token_data = response.json()
        return TokenResponse(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),  # May be None
            expires_at=datetime.utcnow()
            + timedelta(seconds=token_data.get("expires_in", 3600)),
            token_type=token_data.get("token_type", "Bearer"),
            scope=token_data.get("scope", ""),
        )

    async def get_user_info(self, access_token: str) -> UserInfo:
        """Get user information from Google.

        Args:
            access_token: Valid access token.

        Returns:
            UserInfo with email and optional profile data.

        Raises:
            AuthError: If request fails.
        """
        client = await self._get_client()

        try:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except httpx.RequestError as e:
            raise AuthError(
                message=f"Failed to fetch user info: {e}",
                code="oauth_failed",
                details={"error": str(e)},
            ) from e

        if response.status_code != 200:
            raise AuthError(
                message="Failed to fetch user info from Google",
                code="oauth_failed",
                details={"status_code": response.status_code},
            )

        data = response.json()
        return UserInfo(
            email=data["email"],
            verified_email=data.get("verified_email", False),
            name=data.get("name"),
            picture=data.get("picture"),
        )

    async def revoke_token(self, token: str) -> bool:
        """Revoke a token (access or refresh).

        Args:
            token: Token to revoke.

        Returns:
            True if revocation succeeded, False otherwise.
        """
        client = await self._get_client()

        try:
            response = await client.post(
                GOOGLE_REVOKE_URL,
                data={"token": token},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False

    @staticmethod
    def _parse_token_response(data: dict) -> TokenResponse:
        """Parse token response from Google.

        Args:
            data: JSON response from token endpoint.

        Returns:
            Parsed TokenResponse.
        """
        expires_in = data.get("expires_in", 3600)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        return TokenResponse(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope", ""),
        )
