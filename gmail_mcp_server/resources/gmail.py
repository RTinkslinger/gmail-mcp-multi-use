"""Gmail-related MCP resources.

These resources provide Gmail account information like labels and profiles.
"""

from __future__ import annotations

import json

from gmail_mcp_server.server import mcp, state


@mcp.resource("gmail://{connection_id}/labels")
async def get_gmail_labels(connection_id: str) -> str:
    """Get all labels for a Gmail connection.

    Args:
        connection_id: The connection ID.

    Returns JSON list of labels with:
    - id: label ID
    - name: label name
    - type: "system" or "user"
    - message_count: number of messages (may be null)
    - unread_count: number of unread messages (may be null)
    """
    await state.initialize()

    try:
        labels = await state.gmail_service.list_labels(connection_id)

        result = []
        for label in labels:
            result.append({
                "id": label.id,
                "name": label.name,
                "type": label.type,
                "message_count": label.message_count,
                "unread_count": label.unread_count,
            })

        return json.dumps(result, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("gmail://{connection_id}/profile")
async def get_gmail_profile(connection_id: str) -> str:
    """Get Gmail profile info for a connection.

    Args:
        connection_id: The connection ID.

    Returns JSON with:
    - email_address: the Gmail address
    - messages_total: total number of messages
    - threads_total: total number of threads
    - history_id: current history ID
    """
    await state.initialize()

    try:
        profile = await state.gmail_service.get_profile(connection_id)
        return json.dumps(profile, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})
