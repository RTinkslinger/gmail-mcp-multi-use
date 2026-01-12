"""Mock Google OAuth client for sandbox mode.

Simulates Google OAuth without making real API calls.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from gmail_multi_user.sandbox.mode import get_sandbox_config


@dataclass
class MockTokenResponse:
    """Mock token response from OAuth flow."""

    access_token: str
    refresh_token: str | None
    expires_at: datetime
    token_type: str = "Bearer"


@dataclass
class MockUserInfo:
    """Mock user info from Google."""

    email: str
    name: str
    picture: str | None = None


class MockGoogleOAuthClient:
    """Mock Google OAuth client for sandbox mode.

    Simulates the OAuth flow without making real API calls.
    Generates fake tokens and user info for testing.

    Example:
        client = MockGoogleOAuthClient()
        url = client.build_auth_url(state="abc123", code_challenge="xyz")
        # User "authorizes"
        tokens = await client.exchange_code(code="fake_code", code_verifier="xyz")
        user = await client.get_user_info(tokens.access_token)
    """

    def __init__(self, config: dict | None = None) -> None:
        """Initialize mock OAuth client.

        Args:
            config: Optional configuration dict (ignored in mock).
        """
        self._sandbox_config = get_sandbox_config()

    async def close(self) -> None:
        """Close resources (no-op for mock)."""
        pass

    def build_auth_url(
        self,
        state: str,
        code_challenge: str,
        scopes: list[str] | None = None,
        redirect_uri: str | None = None,
    ) -> str:
        """Build a mock authorization URL.

        Args:
            state: OAuth state parameter.
            code_challenge: PKCE code challenge.
            scopes: OAuth scopes.
            redirect_uri: Redirect URI.

        Returns:
            Mock authorization URL (not a real Google URL).
        """
        # Return a fake auth URL that indicates sandbox mode
        return f"https://sandbox.example.com/oauth/authorize?state={state}&sandbox=true"

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        redirect_uri: str | None = None,
    ) -> MockTokenResponse:
        """Exchange authorization code for tokens.

        In sandbox mode, this always succeeds with mock tokens.

        Args:
            code: Authorization code (ignored in sandbox).
            code_verifier: PKCE verifier (ignored in sandbox).
            redirect_uri: Redirect URI (ignored in sandbox).

        Returns:
            MockTokenResponse with fake tokens.
        """
        # Simulate some latency
        import asyncio

        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        return MockTokenResponse(
            access_token=f"sandbox_access_{secrets.token_hex(16)}",
            refresh_token=f"sandbox_refresh_{secrets.token_hex(16)}",
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

    async def refresh_access_token(
        self,
        refresh_token: str,
    ) -> MockTokenResponse:
        """Refresh an access token.

        In sandbox mode, this always succeeds with new mock tokens.

        Args:
            refresh_token: Refresh token.

        Returns:
            MockTokenResponse with new fake tokens.
        """
        import asyncio

        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        return MockTokenResponse(
            access_token=f"sandbox_access_{secrets.token_hex(16)}",
            refresh_token=None,  # Google doesn't always return new refresh token
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )

    async def get_user_info(self, access_token: str) -> MockUserInfo:
        """Get user info from token.

        In sandbox mode, returns the configured mock user.

        Args:
            access_token: Access token.

        Returns:
            MockUserInfo with sandbox user details.
        """
        import asyncio

        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        return MockUserInfo(
            email=self._sandbox_config.default_user_email,
            name=self._sandbox_config.default_user_name,
        )

    async def revoke_token(self, token: str) -> None:
        """Revoke a token.

        In sandbox mode, this is a no-op that always succeeds.

        Args:
            token: Token to revoke.
        """
        import asyncio

        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)
        # Always succeeds in sandbox mode
