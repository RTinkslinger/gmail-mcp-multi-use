"""Gmail read operation MCP tools.

These tools handle reading emails, threads, and attachments.
"""

from __future__ import annotations

import base64
from typing import Any, Literal

from gmail_mcp_server.server import mcp, state, format_response


def format_message(msg: Any) -> dict[str, Any]:
    """Format a Message object for MCP output."""
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "subject": msg.subject,
        "from": {
            "name": msg.from_.name,
            "email": msg.from_.email,
        },
        "to": [{"name": c.name, "email": c.email} for c in msg.to],
        "cc": [{"name": c.name, "email": c.email} for c in msg.cc],
        "bcc": [{"name": c.name, "email": c.email} for c in msg.bcc],
        "date": msg.date.isoformat() if msg.date else None,
        "snippet": msg.snippet,
        "body_plain": msg.body_plain,
        "body_html": msg.body_html,
        "labels": msg.labels,
        "has_attachments": msg.has_attachments,
        "attachments": [
            {
                "id": att.id,
                "filename": att.filename,
                "mime_type": att.mime_type,
                "size": att.size,
            }
            for att in msg.attachments
        ],
    }


@mcp.tool
async def gmail_search(
    connection_id: str,
    query: str,
    max_results: int = 10,
    include_body: bool = False,
) -> dict[str, Any]:
    """Search emails using Gmail query syntax.

    Args:
        connection_id: Gmail connection to search.
        query: Gmail search query (e.g., "is:unread from:boss").
        max_results: Maximum results (1-100).
        include_body: Include message body in results (slower).

    Returns:
        Dictionary with messages list and total_estimate.
    """
    await state.initialize()

    # Clamp max_results
    max_results = max(1, min(100, max_results))

    result = await state.gmail_service.search(
        connection_id=connection_id,
        query=query,
        max_results=max_results,
        include_body=include_body,
    )

    return {
        "messages": [format_message(msg) for msg in result.messages],
        "total_estimate": result.total_estimate,
        "next_page_token": result.next_page_token,
    }


@mcp.tool
async def gmail_get_message(
    connection_id: str,
    message_id: str,
    format: Literal["full", "metadata", "minimal"] = "full",
) -> dict[str, Any]:
    """Get single message with full content.

    Args:
        connection_id: Gmail connection.
        message_id: ID of the message to retrieve.
        format: Detail level - "full" (default), "metadata", or "minimal".

    Returns:
        Full Message object.
    """
    await state.initialize()

    message = await state.gmail_service.get_message(
        connection_id=connection_id,
        message_id=message_id,
        format=format,
    )

    return format_message(message)


@mcp.tool
async def gmail_get_thread(
    connection_id: str,
    thread_id: str,
) -> dict[str, Any]:
    """Get all messages in a thread.

    Args:
        connection_id: Gmail connection.
        thread_id: ID of the thread to retrieve.

    Returns:
        Thread object with messages list.
    """
    await state.initialize()

    thread = await state.gmail_service.get_thread(
        connection_id=connection_id,
        thread_id=thread_id,
    )

    return {
        "id": thread.id,
        "subject": thread.subject,
        "message_count": thread.message_count,
        "messages": [format_message(msg) for msg in thread.messages],
    }


@mcp.tool
async def gmail_get_attachment(
    connection_id: str,
    message_id: str,
    attachment_id: str,
) -> dict[str, Any]:
    """Download attachment.

    Args:
        connection_id: Gmail connection.
        message_id: ID of the message containing the attachment.
        attachment_id: ID of the attachment to download.

    Returns:
        Dictionary with filename, mime_type, size, and content_base64.
    """
    await state.initialize()

    attachment = await state.gmail_service.get_attachment(
        connection_id=connection_id,
        message_id=message_id,
        attachment_id=attachment_id,
    )

    # Encode content as base64 for transport
    content_base64 = base64.b64encode(attachment.data).decode("utf-8")

    return {
        "filename": attachment.filename,
        "mime_type": attachment.mime_type,
        "size": attachment.size,
        "content_base64": content_base64,
    }
