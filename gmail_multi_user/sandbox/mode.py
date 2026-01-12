"""Sandbox mode configuration and state management.

Controls whether the library operates in sandbox mode for testing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# Global sandbox state
_sandbox_enabled: bool = False
_sandbox_config: "SandboxConfig | None" = None


@dataclass
class SandboxConfig:
    """Configuration for sandbox mode behavior.

    Attributes:
        default_user_email: Email used for mock authentication.
        default_user_name: Display name for mock user.
        message_count: Number of mock messages to generate.
        thread_count: Number of mock threads.
        simulate_errors: Whether to occasionally simulate API errors.
        error_rate: Probability of simulated errors (0.0-1.0).
        latency_ms: Simulated API latency in milliseconds.
    """

    default_user_email: str = "sandbox@example.com"
    default_user_name: str = "Sandbox User"
    message_count: int = 50
    thread_count: int = 25
    simulate_errors: bool = False
    error_rate: float = 0.05
    latency_ms: int = 100
    custom_messages: list[dict[str, Any]] = field(default_factory=list)


def is_sandbox_mode() -> bool:
    """Check if sandbox mode is enabled.

    Sandbox mode can be enabled via:
    1. GMAIL_MCP_SANDBOX=true environment variable
    2. Programmatically via enable_sandbox_mode()

    Returns:
        True if sandbox mode is active.
    """
    global _sandbox_enabled

    # Check environment variable
    env_sandbox = os.environ.get("GMAIL_MCP_SANDBOX", "").lower()
    if env_sandbox in ("true", "1", "yes"):
        return True

    return _sandbox_enabled


def enable_sandbox_mode(config: SandboxConfig | None = None) -> None:
    """Enable sandbox mode programmatically.

    Args:
        config: Optional custom sandbox configuration.
    """
    global _sandbox_enabled, _sandbox_config
    _sandbox_enabled = True
    _sandbox_config = config or SandboxConfig()


def disable_sandbox_mode() -> None:
    """Disable sandbox mode."""
    global _sandbox_enabled, _sandbox_config
    _sandbox_enabled = False
    _sandbox_config = None


def get_sandbox_config() -> SandboxConfig:
    """Get the current sandbox configuration.

    Returns:
        SandboxConfig instance (creates default if none set).
    """
    global _sandbox_config
    if _sandbox_config is None:
        _sandbox_config = SandboxConfig()
    return _sandbox_config
