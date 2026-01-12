"""PKCE (Proof Key for Code Exchange) implementation.

This module implements RFC 7636 PKCE for secure OAuth 2.0 authorization
code flows. PKCE prevents authorization code interception attacks.

Reference: https://tools.ietf.org/html/rfc7636
"""

from __future__ import annotations

import base64
import hashlib
import secrets


class PKCE:
    """PKCE code verifier and challenge generator.

    PKCE adds a cryptographic challenge to the OAuth flow:
    1. Client generates a random code_verifier
    2. Client computes code_challenge = BASE64URL(SHA256(code_verifier))
    3. Client sends code_challenge with authorization request
    4. Client sends code_verifier with token exchange
    5. Server verifies that SHA256(code_verifier) == code_challenge

    Example:
        pkce = PKCE.generate()
        # Use pkce.code_challenge in authorization URL
        # Use pkce.code_verifier in token exchange
    """

    # RFC 7636 requirements
    MIN_VERIFIER_LENGTH = 43
    MAX_VERIFIER_LENGTH = 128
    DEFAULT_VERIFIER_LENGTH = 64

    def __init__(self, code_verifier: str) -> None:
        """Initialize PKCE with a code verifier.

        Args:
            code_verifier: The PKCE code verifier string.

        Raises:
            ValueError: If the verifier doesn't meet RFC 7636 requirements.
        """
        self._validate_verifier(code_verifier)
        self._code_verifier = code_verifier
        self._code_challenge = self._compute_challenge(code_verifier)

    @property
    def code_verifier(self) -> str:
        """Get the code verifier (sent during token exchange)."""
        return self._code_verifier

    @property
    def code_challenge(self) -> str:
        """Get the code challenge (sent during authorization)."""
        return self._code_challenge

    @property
    def code_challenge_method(self) -> str:
        """Get the code challenge method (always S256)."""
        return "S256"

    @classmethod
    def generate(cls, length: int = DEFAULT_VERIFIER_LENGTH) -> PKCE:
        """Generate a new PKCE instance with random verifier.

        Args:
            length: Length of the code verifier (43-128, default 64).

        Returns:
            New PKCE instance with generated verifier and challenge.

        Raises:
            ValueError: If length is outside RFC 7636 bounds.
        """
        if length < cls.MIN_VERIFIER_LENGTH or length > cls.MAX_VERIFIER_LENGTH:
            raise ValueError(
                f"Verifier length must be between {cls.MIN_VERIFIER_LENGTH} "
                f"and {cls.MAX_VERIFIER_LENGTH}, got {length}"
            )

        code_verifier = cls._generate_verifier(length)
        return cls(code_verifier)

    @staticmethod
    def _generate_verifier(length: int) -> str:
        """Generate a cryptographically random code verifier.

        Uses URL-safe characters as per RFC 7636:
        [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"

        Args:
            length: Desired length of the verifier.

        Returns:
            Random code verifier string.
        """
        # Use secrets.token_urlsafe which produces URL-safe base64
        # Each base64 character encodes 6 bits, so we need ceiling(length * 6 / 8) bytes
        num_bytes = (length * 6 + 7) // 8
        token = secrets.token_urlsafe(num_bytes)
        # Truncate to exact length (token_urlsafe may produce slightly more)
        return token[:length]

    @staticmethod
    def _compute_challenge(code_verifier: str) -> str:
        """Compute the code challenge from code verifier.

        challenge = BASE64URL(SHA256(code_verifier))

        Args:
            code_verifier: The code verifier string.

        Returns:
            Base64url-encoded SHA256 hash (without padding).
        """
        # SHA256 hash of the verifier
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()

        # Base64url encode without padding
        challenge = base64.urlsafe_b64encode(digest).decode("ascii")

        # Remove padding (= characters)
        return challenge.rstrip("=")

    @classmethod
    def _validate_verifier(cls, code_verifier: str) -> None:
        """Validate that a code verifier meets RFC 7636 requirements.

        Args:
            code_verifier: The code verifier to validate.

        Raises:
            ValueError: If the verifier is invalid.
        """
        length = len(code_verifier)

        if length < cls.MIN_VERIFIER_LENGTH:
            raise ValueError(
                f"Code verifier too short: {length} chars "
                f"(minimum {cls.MIN_VERIFIER_LENGTH})"
            )

        if length > cls.MAX_VERIFIER_LENGTH:
            raise ValueError(
                f"Code verifier too long: {length} chars "
                f"(maximum {cls.MAX_VERIFIER_LENGTH})"
            )

        # RFC 7636 allows: [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
        allowed = set(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
        )

        for char in code_verifier:
            if char not in allowed:
                raise ValueError(
                    f"Invalid character in code verifier: {char!r}. "
                    "Only [A-Z], [a-z], [0-9], '-', '.', '_', '~' are allowed."
                )

    @classmethod
    def verify(cls, code_verifier: str, code_challenge: str) -> bool:
        """Verify that a code verifier matches a code challenge.

        This is useful for testing or if you need to verify on the server side.

        Args:
            code_verifier: The code verifier to check.
            code_challenge: The expected code challenge.

        Returns:
            True if the verifier produces the challenge, False otherwise.
        """
        try:
            computed = cls._compute_challenge(code_verifier)
            return secrets.compare_digest(computed, code_challenge)
        except Exception:
            return False
