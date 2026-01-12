"""Gmail write operation MCP tools.

These tools handle sending emails and managing drafts.
"""

from __future__ import annotations

from typing import Any

from gmail_mcp_server.server import mcp, state


@mcp.tool
async def gmail_send(
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    """Send email.

    Args:
        connection_id: Gmail connection to send from.
        to: List of recipient email addresses.
        subject: Email subject.
        body: Plain text body.
        body_html: Optional HTML body.
        cc: Optional CC recipients.
        bcc: Optional BCC recipients.
        reply_to_message_id: Optional message ID for threading (reply).

    Returns:
        Dictionary with success, message_id, and thread_id.
    """
    await state.initialize()

    # If replying, use the reply method
    if reply_to_message_id:
        result = await state.gmail_service.reply(
            connection_id=connection_id,
            message_id=reply_to_message_id,
            body=body,
            body_html=body_html,
            reply_all=bool(cc),  # If CC provided, treat as reply-all
        )
    else:
        result = await state.gmail_service.send(
            connection_id=connection_id,
            to=to,
            subject=subject,
            body=body,
            body_html=body_html,
            cc=cc,
            bcc=bcc,
        )

    return {
        "success": result.success,
        "message_id": result.message_id,
        "thread_id": result.thread_id,
    }


@mcp.tool
async def gmail_create_draft(
    connection_id: str,
    to: list[str],
    subject: str,
    body: str,
    body_html: str | None = None,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to_message_id: str | None = None,
) -> dict[str, Any]:
    """Create draft email.

    Args:
        connection_id: Gmail connection.
        to: List of recipient email addresses.
        subject: Email subject.
        body: Plain text body.
        body_html: Optional HTML body.
        cc: Optional CC recipients.
        bcc: Optional BCC recipients.
        reply_to_message_id: Optional message ID for threading (reply draft).

    Returns:
        Dictionary with draft_id and message_id.
    """
    await state.initialize()

    # Get thread_id if replying
    thread_id: str | None = None
    if reply_to_message_id:
        original = await state.gmail_service.get_message(
            connection_id=connection_id,
            message_id=reply_to_message_id,
            format="minimal",
        )
        thread_id = original.thread_id

    result = await state.gmail_service.create_draft(
        connection_id=connection_id,
        to=to,
        subject=subject,
        body=body,
        body_html=body_html,
        cc=cc,
        bcc=bcc,
        thread_id=thread_id,
    )

    return {
        "draft_id": result.draft_id,
        "message_id": result.message_id,
    }


@mcp.tool
async def gmail_send_draft(
    connection_id: str,
    draft_id: str,
) -> dict[str, Any]:
    """Send existing draft.

    Args:
        connection_id: Gmail connection.
        draft_id: ID of the draft to send.

    Returns:
        Dictionary with success, message_id, and thread_id.
    """
    await state.initialize()

    result = await state.gmail_service.send_draft(
        connection_id=connection_id,
        draft_id=draft_id,
    )

    return {
        "success": result.success,
        "message_id": result.message_id,
        "thread_id": result.thread_id,
    }
