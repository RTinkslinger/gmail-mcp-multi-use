"""Gmail service orchestration layer.

This module provides the high-level service layer that coordinates
token management, Gmail API calls, and connection updates.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from gmail_multi_user.gmail.client import GmailAPIClient
from gmail_multi_user.logging import LogContext, get_logger

logger = get_logger(__name__)
from gmail_multi_user.gmail.composer import MessageComposer
from gmail_multi_user.gmail.parser import MessageParser, decode_attachment_data
from gmail_multi_user.types import (
    AttachmentData,
    AttachmentInput,
    DraftResult,
    Label,
    Message,
    SearchResult,
    SendResult,
    Thread,
)

if TYPE_CHECKING:
    from gmail_multi_user.config import Config
    from gmail_multi_user.storage.base import StorageBackend
    from gmail_multi_user.tokens.encryption import TokenEncryption
    from gmail_multi_user.tokens.manager import TokenManager


class GmailService:
    """High-level Gmail service for read operations.

    This service:
    - Manages token retrieval and auto-refresh
    - Coordinates Gmail API calls
    - Parses responses into domain objects
    - Updates connection last_used_at timestamps

    Example:
        service = GmailService(config, storage, token_manager)
        result = await service.search(connection_id, query="is:unread")
    """

    def __init__(
        self,
        config: Config,
        storage: StorageBackend,
        token_manager: TokenManager,
    ) -> None:
        """Initialize the Gmail service.

        Args:
            config: Application configuration.
            storage: Storage backend.
            token_manager: Token manager for access tokens.
        """
        self._config = config
        self._storage = storage
        self._token_manager = token_manager
        self._api_client = GmailAPIClient()
        self._parser = MessageParser()
        self._composer = MessageComposer()

    async def close(self) -> None:
        """Close resources."""
        await self._api_client.close()

    async def _get_token(self, connection_id: str) -> str:
        """Get a valid access token for a connection.

        Args:
            connection_id: Connection ID.

        Returns:
            Valid access token.

        Raises:
            ConnectionNotFoundError: If connection doesn't exist.
            ConnectionInactiveError: If connection is inactive.
            TokenError: If token refresh fails.
        """
        valid_token = await self._token_manager.get_valid_token(connection_id)
        return valid_token.access_token

    async def _update_last_used(self, connection_id: str) -> None:
        """Update the last_used_at timestamp for a connection.

        Args:
            connection_id: Connection ID.
        """
        await self._storage.update_connection_last_used(connection_id)

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search(
        self,
        connection_id: str,
        query: str,
        max_results: int = 10,
        include_body: bool = False,
        page_token: str | None = None,
    ) -> SearchResult:
        """Search emails using Gmail query syntax.

        Args:
            connection_id: Gmail connection to search.
            query: Gmail search query (e.g., "is:unread from:boss").
            max_results: Maximum results (1-100).
            include_body: Include message body in results.
            page_token: Token for pagination.

        Returns:
            SearchResult with messages and pagination info.
        """
        with LogContext(connection_id=connection_id, operation="search"):
            logger.info("Searching messages", query=query, max_results=max_results)
            token = await self._get_token(connection_id)

            # Search for message IDs
            search_result = await self._api_client.search(
                token=token,
                query=query,
                max_results=max_results,
                page_token=page_token,
            )

            message_refs = search_result.get("messages", [])
            next_page = search_result.get("nextPageToken")
            total_estimate = search_result.get("resultSizeEstimate", 0)

            if not message_refs:
                await self._update_last_used(connection_id)
                logger.debug("Search returned no results")
                return SearchResult(
                    messages=[],
                    next_page_token=next_page,
                    total_estimate=total_estimate,
                )

            # Fetch message details
            message_ids = [m["id"] for m in message_refs]
            format_type: Literal["full", "metadata"] = "full" if include_body else "metadata"

            raw_messages = await self._api_client.batch_get_messages(
                token=token,
                message_ids=message_ids,
                format=format_type,
            )

            # Parse messages
            messages = []
            for raw_msg in raw_messages:
                if include_body:
                    msg = self._parser.parse(raw_msg)
                else:
                    msg = self._parser.parse_metadata(raw_msg)
                messages.append(msg)

            await self._update_last_used(connection_id)
            logger.info("Search completed", result_count=len(messages), total_estimate=total_estimate)

            return SearchResult(
                messages=messages,
                next_page_token=next_page,
                total_estimate=total_estimate,
            )

    # =========================================================================
    # Message Operations
    # =========================================================================

    async def get_message(
        self,
        connection_id: str,
        message_id: str,
        format: Literal["full", "metadata", "minimal"] = "full",
    ) -> Message:
        """Get a single email message.

        Args:
            connection_id: Gmail connection.
            message_id: ID of the message.
            format: Detail level.

        Returns:
            Message object with full details.
        """
        token = await self._get_token(connection_id)

        raw_message = await self._api_client.get_message(
            token=token,
            message_id=message_id,
            format=format,
        )

        if format == "full":
            message = self._parser.parse(raw_message)
        elif format == "metadata":
            message = self._parser.parse_metadata(raw_message)
        else:
            message = self._parser.parse_minimal(raw_message)

        await self._update_last_used(connection_id)

        return message

    async def batch_get_messages(
        self,
        connection_id: str,
        message_ids: list[str],
        format: Literal["full", "metadata", "minimal"] = "metadata",
    ) -> list[Message]:
        """Get multiple messages efficiently.

        Args:
            connection_id: Gmail connection.
            message_ids: List of message IDs.
            format: Detail level.

        Returns:
            List of Message objects.
        """
        token = await self._get_token(connection_id)

        raw_messages = await self._api_client.batch_get_messages(
            token=token,
            message_ids=message_ids,
            format=format,
        )

        messages = []
        for raw_msg in raw_messages:
            if format == "full":
                msg = self._parser.parse(raw_msg)
            elif format == "metadata":
                msg = self._parser.parse_metadata(raw_msg)
            else:
                msg = self._parser.parse_minimal(raw_msg)
            messages.append(msg)

        await self._update_last_used(connection_id)

        return messages

    # =========================================================================
    # Thread Operations
    # =========================================================================

    async def get_thread(
        self,
        connection_id: str,
        thread_id: str,
    ) -> Thread:
        """Get all messages in an email thread.

        Args:
            connection_id: Gmail connection.
            thread_id: ID of the thread.

        Returns:
            Thread object with all messages.
        """
        token = await self._get_token(connection_id)

        raw_thread = await self._api_client.get_thread(
            token=token,
            thread_id=thread_id,
            format="full",
        )

        # Parse all messages in thread
        messages = []
        for raw_msg in raw_thread.get("messages", []):
            msg = self._parser.parse(raw_msg)
            messages.append(msg)

        # Get subject from first message
        subject = messages[0].subject if messages else ""

        await self._update_last_used(connection_id)

        return Thread(
            id=raw_thread.get("id", ""),
            subject=subject,
            message_count=len(messages),
            messages=messages,
        )

    # =========================================================================
    # Label Operations
    # =========================================================================

    async def list_labels(self, connection_id: str) -> list[Label]:
        """List all labels for a Gmail account.

        Args:
            connection_id: Gmail connection.

        Returns:
            List of Label objects.
        """
        token = await self._get_token(connection_id)

        raw_labels = await self._api_client.list_labels(token)

        labels = []
        for raw_label in raw_labels.get("labels", []):
            label_type: Literal["system", "user"] = (
                "system" if raw_label.get("type") == "system" else "user"
            )

            labels.append(
                Label(
                    id=raw_label.get("id", ""),
                    name=raw_label.get("name", ""),
                    type=label_type,
                    message_count=raw_label.get("messagesTotal"),
                    unread_count=raw_label.get("messagesUnread"),
                )
            )

        await self._update_last_used(connection_id)

        return labels

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    async def get_attachment(
        self,
        connection_id: str,
        message_id: str,
        attachment_id: str,
    ) -> AttachmentData:
        """Download an attachment.

        Args:
            connection_id: Gmail connection.
            message_id: ID of the message.
            attachment_id: ID of the attachment.

        Returns:
            AttachmentData with filename, mime_type, and data bytes.
        """
        token = await self._get_token(connection_id)

        # First get the message to find attachment metadata
        raw_message = await self._api_client.get_message(
            token=token,
            message_id=message_id,
            format="full",
        )

        # Find the attachment in the message
        message = self._parser.parse(raw_message)
        attachment_meta = None
        for att in message.attachments:
            if att.id == attachment_id:
                attachment_meta = att
                break

        # Get the attachment data
        raw_attachment = await self._api_client.get_attachment(
            token=token,
            message_id=message_id,
            attachment_id=attachment_id,
        )

        data = decode_attachment_data(raw_attachment.get("data", ""))
        size = raw_attachment.get("size", len(data))

        await self._update_last_used(connection_id)

        return AttachmentData(
            filename=attachment_meta.filename if attachment_meta else "attachment",
            mime_type=attachment_meta.mime_type if attachment_meta else "application/octet-stream",
            size=size,
            data=data,
        )

    # =========================================================================
    # Profile Operations
    # =========================================================================

    async def get_profile(
        self,
        connection_id: str,
    ) -> dict:
        """Get Gmail profile information.

        Args:
            connection_id: Gmail connection.

        Returns:
            Dict with email_address, messages_total, threads_total, history_id.
        """
        token = await self._get_token(connection_id)

        profile = await self._api_client.get_profile(token)

        await self._update_last_used(connection_id)

        return {
            "email_address": profile.get("emailAddress", ""),
            "messages_total": profile.get("messagesTotal", 0),
            "threads_total": profile.get("threadsTotal", 0),
            "history_id": profile.get("historyId", ""),
        }

    # =========================================================================
    # Send Operations
    # =========================================================================

    async def send(
        self,
        connection_id: str,
        to: list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[AttachmentInput] | None = None,
        thread_id: str | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
    ) -> SendResult:
        """Send an email message.

        Args:
            connection_id: Gmail connection.
            to: Recipient email addresses.
            subject: Email subject.
            body: Plain text body.
            body_html: Optional HTML body.
            cc: CC recipients.
            bcc: BCC recipients.
            attachments: List of attachments.
            thread_id: Thread ID for replies.
            in_reply_to: Message-ID for reply threading.
            references: References header for threading.

        Returns:
            SendResult with message_id and thread_id.
        """
        with LogContext(connection_id=connection_id, operation="send"):
            logger.info(
                "Sending message",
                to_count=len(to),
                has_html=body_html is not None,
                attachment_count=len(attachments) if attachments else 0,
            )
            token = await self._get_token(connection_id)

            raw_message = self._composer.compose(
                to=to,
                subject=subject,
                body=body,
                body_html=body_html,
                cc=cc,
                bcc=bcc,
                attachments=attachments,
                in_reply_to=in_reply_to,
                references=references,
            )

            result = await self._api_client.send_message(
                token=token,
                raw_message=raw_message,
                thread_id=thread_id,
            )

            await self._update_last_used(connection_id)
            logger.info("Message sent", message_id=result.get("id", ""))

            return SendResult(
                success=True,
                message_id=result.get("id", ""),
                thread_id=result.get("threadId", ""),
            )

    async def reply(
        self,
        connection_id: str,
        message_id: str,
        body: str,
        body_html: str | None = None,
        reply_all: bool = False,
        attachments: list[AttachmentInput] | None = None,
    ) -> SendResult:
        """Reply to an existing message.

        Args:
            connection_id: Gmail connection.
            message_id: ID of message to reply to.
            body: Reply body text.
            body_html: Optional HTML body.
            reply_all: Include all original recipients.
            attachments: Optional attachments.

        Returns:
            SendResult with message_id and thread_id.
        """
        token = await self._get_token(connection_id)

        # Get the original message
        original = await self.get_message(connection_id, message_id, format="full")

        # Compose reply
        raw_message, thread_id = self._composer.compose_reply(
            original_message=original,
            body=body,
            body_html=body_html,
            reply_all=reply_all,
            attachments=attachments,
        )

        result = await self._api_client.send_message(
            token=token,
            raw_message=raw_message,
            thread_id=thread_id,
        )

        await self._update_last_used(connection_id)

        return SendResult(
            success=True,
            message_id=result.get("id", ""),
            thread_id=result.get("threadId", ""),
        )

    # =========================================================================
    # Draft Operations
    # =========================================================================

    async def create_draft(
        self,
        connection_id: str,
        to: list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[AttachmentInput] | None = None,
        thread_id: str | None = None,
    ) -> DraftResult:
        """Create a draft email.

        Args:
            connection_id: Gmail connection.
            to: Recipient email addresses.
            subject: Email subject.
            body: Plain text body.
            body_html: Optional HTML body.
            cc: CC recipients.
            bcc: BCC recipients.
            attachments: List of attachments.
            thread_id: Thread ID for reply drafts.

        Returns:
            DraftResult with draft_id and message details.
        """
        token = await self._get_token(connection_id)

        raw_message = self._composer.compose(
            to=to,
            subject=subject,
            body=body,
            body_html=body_html,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
        )

        result = await self._api_client.create_draft(
            token=token,
            raw_message=raw_message,
            thread_id=thread_id,
        )

        await self._update_last_used(connection_id)

        message_data = result.get("message", {})
        return DraftResult(
            draft_id=result.get("id", ""),
            message_id=message_data.get("id", ""),
        )

    async def update_draft(
        self,
        connection_id: str,
        draft_id: str,
        to: list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[AttachmentInput] | None = None,
        thread_id: str | None = None,
    ) -> DraftResult:
        """Update an existing draft.

        Args:
            connection_id: Gmail connection.
            draft_id: ID of draft to update.
            to: Recipient email addresses.
            subject: Email subject.
            body: Plain text body.
            body_html: Optional HTML body.
            cc: CC recipients.
            bcc: BCC recipients.
            attachments: List of attachments.
            thread_id: Thread ID for reply drafts.

        Returns:
            DraftResult with updated draft details.
        """
        token = await self._get_token(connection_id)

        raw_message = self._composer.compose(
            to=to,
            subject=subject,
            body=body,
            body_html=body_html,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
        )

        result = await self._api_client.update_draft(
            token=token,
            draft_id=draft_id,
            raw_message=raw_message,
            thread_id=thread_id,
        )

        await self._update_last_used(connection_id)

        message_data = result.get("message", {})
        return DraftResult(
            draft_id=result.get("id", ""),
            message_id=message_data.get("id", ""),
        )

    async def send_draft(
        self,
        connection_id: str,
        draft_id: str,
    ) -> SendResult:
        """Send an existing draft.

        Args:
            connection_id: Gmail connection.
            draft_id: ID of draft to send.

        Returns:
            SendResult with sent message details.
        """
        token = await self._get_token(connection_id)

        result = await self._api_client.send_draft(
            token=token,
            draft_id=draft_id,
        )

        await self._update_last_used(connection_id)

        return SendResult(
            success=True,
            message_id=result.get("id", ""),
            thread_id=result.get("threadId", ""),
        )

    async def delete_draft(
        self,
        connection_id: str,
        draft_id: str,
    ) -> None:
        """Delete a draft.

        Args:
            connection_id: Gmail connection.
            draft_id: ID of draft to delete.
        """
        token = await self._get_token(connection_id)

        await self._api_client.delete_draft(
            token=token,
            draft_id=draft_id,
        )

        await self._update_last_used(connection_id)

    # =========================================================================
    # Label Modification Operations
    # =========================================================================

    async def modify_labels(
        self,
        connection_id: str,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> Message:
        """Modify labels on a message.

        Args:
            connection_id: Gmail connection.
            message_id: Message ID to modify.
            add_labels: Label IDs to add.
            remove_labels: Label IDs to remove.

        Returns:
            Updated Message object.
        """
        token = await self._get_token(connection_id)

        result = await self._api_client.modify_message_labels(
            token=token,
            message_id=message_id,
            add_labels=add_labels,
            remove_labels=remove_labels,
        )

        await self._update_last_used(connection_id)

        return self._parser.parse_minimal(result)

    async def batch_modify_labels(
        self,
        connection_id: str,
        message_ids: list[str],
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> None:
        """Modify labels on multiple messages.

        Args:
            connection_id: Gmail connection.
            message_ids: List of message IDs to modify.
            add_labels: Label IDs to add.
            remove_labels: Label IDs to remove.
        """
        token = await self._get_token(connection_id)

        await self._api_client.batch_modify_labels(
            token=token,
            message_ids=message_ids,
            add_labels=add_labels,
            remove_labels=remove_labels,
        )

        await self._update_last_used(connection_id)

    async def archive(
        self,
        connection_id: str,
        message_id: str,
    ) -> Message:
        """Archive a message (remove from INBOX).

        Args:
            connection_id: Gmail connection.
            message_id: Message ID to archive.

        Returns:
            Updated Message object.
        """
        return await self.modify_labels(
            connection_id=connection_id,
            message_id=message_id,
            remove_labels=["INBOX"],
        )

    async def mark_read(
        self,
        connection_id: str,
        message_ids: list[str],
    ) -> None:
        """Mark messages as read.

        Args:
            connection_id: Gmail connection.
            message_ids: List of message IDs to mark as read.
        """
        if len(message_ids) == 1:
            await self.modify_labels(
                connection_id=connection_id,
                message_id=message_ids[0],
                remove_labels=["UNREAD"],
            )
        else:
            await self.batch_modify_labels(
                connection_id=connection_id,
                message_ids=message_ids,
                remove_labels=["UNREAD"],
            )

    async def mark_unread(
        self,
        connection_id: str,
        message_ids: list[str],
    ) -> None:
        """Mark messages as unread.

        Args:
            connection_id: Gmail connection.
            message_ids: List of message IDs to mark as unread.
        """
        if len(message_ids) == 1:
            await self.modify_labels(
                connection_id=connection_id,
                message_id=message_ids[0],
                add_labels=["UNREAD"],
            )
        else:
            await self.batch_modify_labels(
                connection_id=connection_id,
                message_ids=message_ids,
                add_labels=["UNREAD"],
            )

    # =========================================================================
    # Trash Operations
    # =========================================================================

    async def trash(
        self,
        connection_id: str,
        message_id: str,
    ) -> Message:
        """Move a message to trash.

        Args:
            connection_id: Gmail connection.
            message_id: Message ID to trash.

        Returns:
            Updated Message object.
        """
        token = await self._get_token(connection_id)

        result = await self._api_client.trash_message(
            token=token,
            message_id=message_id,
        )

        await self._update_last_used(connection_id)

        return self._parser.parse_minimal(result)

    async def untrash(
        self,
        connection_id: str,
        message_id: str,
    ) -> Message:
        """Remove a message from trash.

        Args:
            connection_id: Gmail connection.
            message_id: Message ID to untrash.

        Returns:
            Updated Message object.
        """
        token = await self._get_token(connection_id)

        result = await self._api_client.untrash_message(
            token=token,
            message_id=message_id,
        )

        await self._update_last_used(connection_id)

        return self._parser.parse_minimal(result)
