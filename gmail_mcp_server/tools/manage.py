"""Gmail management operation MCP tools.

These tools handle label management, archiving, and trash operations.
"""

from __future__ import annotations

from typing import Any

from gmail_mcp_server.server import mcp, state


@mcp.tool
async def gmail_modify_labels(
    connection_id: str,
    message_id: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
) -> dict[str, Any]:
    """Add/remove labels from message.

    Args:
        connection_id: Gmail connection.
        message_id: ID of the message to modify.
        add_labels: Label IDs to add.
        remove_labels: Label IDs to remove.

    Returns:
        Dictionary with success and current_labels list.
    """
    await state.initialize()

    message = await state.gmail_service.modify_labels(
        connection_id=connection_id,
        message_id=message_id,
        add_labels=add_labels,
        remove_labels=remove_labels,
    )

    return {
        "success": True,
        "current_labels": message.labels,
    }


@mcp.tool
async def gmail_archive(
    connection_id: str,
    message_id: str,
) -> dict[str, Any]:
    """Archive message (remove from inbox).

    Args:
        connection_id: Gmail connection.
        message_id: ID of the message to archive.

    Returns:
        Dictionary with success flag.
    """
    await state.initialize()

    await state.gmail_service.archive(
        connection_id=connection_id,
        message_id=message_id,
    )

    return {"success": True}


@mcp.tool
async def gmail_trash(
    connection_id: str,
    message_id: str,
) -> dict[str, Any]:
    """Move message to trash.

    Args:
        connection_id: Gmail connection.
        message_id: ID of the message to trash.

    Returns:
        Dictionary with success flag.
    """
    await state.initialize()

    await state.gmail_service.trash(
        connection_id=connection_id,
        message_id=message_id,
    )

    return {"success": True}
