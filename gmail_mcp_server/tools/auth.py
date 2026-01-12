"""OAuth and user management MCP tools.

These tools handle OAuth flows and user/connection management.

Each tool has an _impl function that contains the actual logic.
CLI commands use the _impl functions directly, while MCP tools wrap them.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from gmail_mcp_server.server import format_datetime, mcp, state

# =============================================================================
# Implementation Functions (used by both MCP tools and CLI)
# =============================================================================


async def list_connections_impl(
    user_id: str | None = None,
    include_inactive: bool = False,
) -> dict[str, Any]:
    """List Gmail connections."""
    await state.initialize()

    # If user_id provided, get the internal user ID first
    internal_user_id: str | None = None
    if user_id:
        user = await state.storage.get_user_by_external_id(user_id)
        if user:
            internal_user_id = user.id

    connections = await state.storage.list_connections(
        user_id=internal_user_id,
        include_inactive=include_inactive,
    )

    # Format connections for output
    connection_list = []
    for conn in connections:
        # Get the external user ID
        user = await state.storage.get_user_by_id(conn.user_id)
        external_user_id = user.external_user_id if user else None

        connection_list.append(
            {
                "id": conn.id,
                "user_id": external_user_id,
                "gmail_address": conn.gmail_address,
                "scopes": conn.scopes,
                "is_active": conn.is_active,
                "created_at": format_datetime(conn.created_at),
                "last_used_at": format_datetime(conn.last_used_at),
            }
        )

    return {"connections": connection_list}


async def check_connection_impl(connection_id: str) -> dict[str, Any]:
    """Check if a connection is valid and working."""
    await state.initialize()

    connection = await state.storage.get_connection(connection_id)

    if not connection:
        return {
            "valid": False,
            "gmail_address": "",
            "scopes": [],
            "token_expires_in": None,
            "needs_reauth": True,
            "error": "Connection not found",
        }

    if not connection.is_active:
        return {
            "valid": False,
            "gmail_address": connection.gmail_address,
            "scopes": connection.scopes,
            "token_expires_in": None,
            "needs_reauth": True,
            "error": "Connection is inactive",
        }

    # Calculate token expiration
    now = datetime.now(timezone.utc)
    expires_in: int | None = None
    needs_reauth = False

    if connection.token_expires_at:
        expires_in = int((connection.token_expires_at - now).total_seconds())
        if expires_in < 0:
            needs_reauth = True

    # Try to validate token by getting a valid one
    error: str | None = None
    try:
        await state.token_manager.get_valid_token(connection_id)
    except Exception as e:
        error = str(e)
        needs_reauth = True

    return {
        "valid": error is None and not needs_reauth,
        "gmail_address": connection.gmail_address,
        "scopes": connection.scopes,
        "token_expires_in": max(0, expires_in) if expires_in else None,
        "needs_reauth": needs_reauth,
        "error": error,
    }


async def disconnect_impl(
    connection_id: str,
    revoke_google_access: bool = True,
) -> dict[str, Any]:
    """Disconnect Gmail account and delete tokens."""
    await state.initialize()

    # Get connection info first
    connection = await state.storage.get_connection(connection_id)
    if not connection:
        return {
            "success": False,
            "gmail_address": "",
            "error": "Connection not found",
        }

    gmail_address = connection.gmail_address

    # Disconnect
    success = await state.oauth_manager.disconnect(
        connection_id=connection_id,
        revoke_google_access=revoke_google_access,
    )

    return {
        "success": success,
        "gmail_address": gmail_address,
    }


# =============================================================================
# MCP Tool Wrappers
# =============================================================================


@mcp.tool
async def gmail_get_auth_url(
    user_id: str,
    scopes: list[str] | None = None,
    redirect_uri: str | None = None,
) -> dict[str, Any]:
    """Generate OAuth URL for user to connect Gmail.

    Args:
        user_id: External user identifier from your application.
        scopes: OAuth scopes to request. Defaults to config scopes.
        redirect_uri: Override the configured redirect URI.

    Returns:
        Dictionary with auth_url, state, and expires_in (seconds).
    """
    await state.initialize()

    result = await state.oauth_manager.get_auth_url(
        user_id=user_id,
        scopes=scopes,
        redirect_uri=redirect_uri,
    )

    # Calculate expires_in from expires_at
    expires_in = int((result.expires_at - datetime.now(timezone.utc)).total_seconds())

    return {
        "auth_url": result.auth_url,
        "state": result.state,
        "expires_in": expires_in,
    }


@mcp.tool
async def gmail_handle_oauth_callback(
    code: str,
    state_param: str,
) -> dict[str, Any]:
    """Process OAuth callback and store tokens.

    Args:
        code: Authorization code from Google.
        state_param: State parameter for CSRF validation.

    Returns:
        Dictionary with success, connection_id, user_id, gmail_address, or error.
    """
    await state.initialize()

    result = await state.oauth_manager.handle_callback(
        code=code,
        state=state_param,
    )

    return {
        "success": result.success,
        "connection_id": result.connection_id,
        "user_id": result.user_id,
        "gmail_address": result.gmail_address,
        "error": result.error,
    }


@mcp.tool
async def gmail_list_connections(
    user_id: str | None = None,
    include_inactive: bool = False,
) -> dict[str, Any]:
    """List Gmail connections.

    Args:
        user_id: Filter by external user ID (optional).
        include_inactive: Include revoked/expired connections.

    Returns:
        Dictionary with list of connections.
    """
    return await list_connections_impl(
        user_id=user_id, include_inactive=include_inactive
    )


@mcp.tool
async def gmail_check_connection(connection_id: str) -> dict[str, Any]:
    """Check if a connection is valid and working.

    Args:
        connection_id: Connection ID to check.

    Returns:
        Dictionary with valid, gmail_address, scopes, token_expires_in,
        needs_reauth, and any error.
    """
    return await check_connection_impl(connection_id=connection_id)


@mcp.tool
async def gmail_disconnect(
    connection_id: str,
    revoke_google_access: bool = True,
) -> dict[str, Any]:
    """Disconnect Gmail account and delete tokens.

    Args:
        connection_id: Connection ID to disconnect.
        revoke_google_access: Also revoke access at Google.

    Returns:
        Dictionary with success and gmail_address.
    """
    return await disconnect_impl(
        connection_id=connection_id,
        revoke_google_access=revoke_google_access,
    )
