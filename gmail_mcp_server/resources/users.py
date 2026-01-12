"""User-related MCP resources.

These resources provide user and connection information.
"""

from __future__ import annotations

import json

from gmail_mcp_server.server import format_datetime, mcp, state


@mcp.resource("users://list")
async def get_users_list() -> str:
    """Get all users with Gmail connections.

    Returns JSON list of users with:
    - id: internal user ID
    - external_user_id: your application's user ID
    - email: user's email
    - connection_count: number of Gmail connections
    - created_at: ISO timestamp
    """
    await state.initialize()

    users = await state.storage.list_users()
    connections = await state.storage.list_connections()

    # Count connections per user
    user_connection_counts: dict[str, int] = {}
    for conn in connections:
        user_connection_counts[conn.user_id] = user_connection_counts.get(conn.user_id, 0) + 1

    result = []
    for user in users:
        result.append({
            "id": user.id,
            "external_user_id": user.external_user_id,
            "email": user.email,
            "connection_count": user_connection_counts.get(user.id, 0),
            "created_at": format_datetime(user.created_at),
        })

    return json.dumps(result, indent=2)


@mcp.resource("users://{user_id}/connections")
async def get_user_connections(user_id: str) -> str:
    """Get all Gmail connections for a specific user.

    Args:
        user_id: The external user ID (your application's user ID).

    Returns JSON list of connections with full details.
    """
    await state.initialize()

    # Look up user by external ID
    user = await state.storage.get_user_by_external_id(user_id)
    if not user:
        return json.dumps({"error": f"User not found: {user_id}"})

    connections = await state.storage.list_connections(
        user_id=user.id,
        include_inactive=True,
    )

    result = []
    for conn in connections:
        result.append({
            "id": conn.id,
            "gmail_address": conn.gmail_address,
            "scopes": conn.scopes,
            "is_active": conn.is_active,
            "created_at": format_datetime(conn.created_at),
            "updated_at": format_datetime(conn.updated_at),
            "last_used_at": format_datetime(conn.last_used_at),
            "token_expires_at": format_datetime(conn.token_expires_at),
        })

    return json.dumps(result, indent=2)
