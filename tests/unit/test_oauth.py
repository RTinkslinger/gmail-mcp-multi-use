"""Tests for OAuth components."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from gmail_multi_user.exceptions import AuthError
from gmail_multi_user.oauth.pkce import PKCE
from gmail_multi_user.oauth.state import OAuthStateManager


class TestPKCE:
    """Tests for PKCE implementation."""

    def test_generate_creates_valid_pkce(self) -> None:
        """Test that generate creates valid PKCE."""
        pkce = PKCE.generate()

        assert len(pkce.code_verifier) == PKCE.DEFAULT_VERIFIER_LENGTH
        assert len(pkce.code_challenge) == 43  # SHA256 -> base64url without padding
        assert pkce.code_challenge_method == "S256"

    def test_generate_custom_length(self) -> None:
        """Test generate with custom length."""
        pkce = PKCE.generate(length=64)
        assert len(pkce.code_verifier) == 64

        pkce = PKCE.generate(length=128)
        assert len(pkce.code_verifier) == 128

    def test_generate_min_length(self) -> None:
        """Test generate with minimum length."""
        pkce = PKCE.generate(length=43)
        assert len(pkce.code_verifier) == 43

    def test_generate_max_length(self) -> None:
        """Test generate with maximum length."""
        pkce = PKCE.generate(length=128)
        assert len(pkce.code_verifier) == 128

    def test_generate_rejects_too_short(self) -> None:
        """Test that generate rejects length < 43."""
        with pytest.raises(ValueError, match="between 43 and 128"):
            PKCE.generate(length=42)

    def test_generate_rejects_too_long(self) -> None:
        """Test that generate rejects length > 128."""
        with pytest.raises(ValueError, match="between 43 and 128"):
            PKCE.generate(length=129)

    def test_verifier_is_unique(self) -> None:
        """Test that each generation produces unique verifier."""
        pkce1 = PKCE.generate()
        pkce2 = PKCE.generate()

        assert pkce1.code_verifier != pkce2.code_verifier
        assert pkce1.code_challenge != pkce2.code_challenge

    def test_challenge_is_deterministic(self) -> None:
        """Test that same verifier produces same challenge."""
        verifier = "a" * 64
        pkce1 = PKCE(verifier)
        pkce2 = PKCE(verifier)

        assert pkce1.code_challenge == pkce2.code_challenge

    def test_verifier_valid_characters(self) -> None:
        """Test that verifier only contains RFC 7636 allowed characters."""
        allowed = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        )

        for _ in range(10):
            pkce = PKCE.generate()
            for char in pkce.code_verifier:
                assert char in allowed, f"Invalid character: {char!r}"

    def test_verify_correct(self) -> None:
        """Test that verify returns True for matching verifier/challenge."""
        pkce = PKCE.generate()
        assert PKCE.verify(pkce.code_verifier, pkce.code_challenge) is True

    def test_verify_incorrect(self) -> None:
        """Test that verify returns False for non-matching."""
        pkce1 = PKCE.generate()
        pkce2 = PKCE.generate()

        assert PKCE.verify(pkce1.code_verifier, pkce2.code_challenge) is False

    def test_invalid_verifier_characters_rejected(self) -> None:
        """Test that invalid characters in verifier are rejected."""
        with pytest.raises(ValueError, match="Invalid character"):
            PKCE("a" * 43 + "!")  # ! is not allowed

    def test_challenge_no_padding(self) -> None:
        """Test that code challenge has no base64 padding."""
        pkce = PKCE.generate()
        assert "=" not in pkce.code_challenge


class TestOAuthStateManager:
    """Tests for OAuth state manager."""

    @pytest.mark.asyncio
    async def test_create_state(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test creating an OAuth state."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend, ttl_seconds=600)

        state = await manager.create_state(
            user_id=user_id,
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
        )

        assert len(state.state) > 0
        assert state.user_id == user_id
        assert state.scopes == ["gmail.readonly"]
        assert len(state.code_verifier) >= 43

    @pytest.mark.asyncio
    async def test_validate_state_valid(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test validating a valid state."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend, ttl_seconds=600)

        created = await manager.create_state(
            user_id=user_id,
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
        )

        validated = await manager.validate_state(created.state)

        assert validated is not None
        assert validated.state == created.state

    @pytest.mark.asyncio
    async def test_validate_state_not_found(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test validating non-existent state."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend)

        result = await manager.validate_state("nonexistent_state")
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_consume_success(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test validating and consuming a state."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend, ttl_seconds=600)

        created = await manager.create_state(
            user_id=user_id,
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
        )

        consumed = await manager.validate_and_consume(created.state)

        assert consumed.state == created.state

        # State should be deleted (single-use)
        result = await manager.validate_state(created.state)
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_and_consume_invalid_state(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test that invalid state raises AuthError."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend)

        with pytest.raises(AuthError) as exc_info:
            await manager.validate_and_consume("invalid_state")

        assert exc_info.value.code == "invalid_state"

    @pytest.mark.asyncio
    async def test_validate_and_consume_expired_state(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test that expired state raises AuthError."""
        backend, user_id = sqlite_backend_with_user
        # Create manager with 0 second TTL (immediately expired)
        manager = OAuthStateManager(backend, ttl_seconds=0)

        created = await manager.create_state(
            user_id=user_id,
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
        )

        # State should be expired immediately
        with pytest.raises(AuthError) as exc_info:
            await manager.validate_and_consume(created.state)

        assert exc_info.value.code == "state_expired"

    @pytest.mark.asyncio
    async def test_state_uniqueness(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test that each state is unique."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend)

        states = set()
        for _ in range(10):
            state = await manager.create_state(
                user_id=user_id,
                scopes=["gmail.readonly"],
                redirect_uri="http://localhost:8000/callback",
            )
            states.add(state.state)

        assert len(states) == 10

    @pytest.mark.asyncio
    async def test_get_pkce_challenge(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test getting PKCE challenge from verifier."""
        backend, user_id = sqlite_backend_with_user
        manager = OAuthStateManager(backend)

        state = await manager.create_state(
            user_id=user_id,
            scopes=["gmail.readonly"],
            redirect_uri="http://localhost:8000/callback",
        )

        challenge = manager.get_pkce_challenge(state.code_verifier)

        # Should match what PKCE would compute
        pkce = PKCE(state.code_verifier)
        assert challenge == pkce.code_challenge

    @pytest.mark.asyncio
    async def test_cleanup_expired(
        self,
        sqlite_backend_with_user: tuple,
    ) -> None:
        """Test cleaning up expired states."""
        backend, user_id = sqlite_backend_with_user

        # Create with 0 TTL (immediately expired)
        manager = OAuthStateManager(backend, ttl_seconds=0)

        # Create some states
        for _ in range(3):
            await manager.create_state(
                user_id=user_id,
                scopes=["gmail.readonly"],
                redirect_uri="http://localhost:8000/callback",
            )

        # Cleanup
        deleted = await manager.cleanup_expired()

        assert deleted == 3
