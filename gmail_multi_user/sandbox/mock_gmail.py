"""Mock Gmail API client for sandbox mode.

Simulates Gmail API responses without making real API calls.
"""

from __future__ import annotations

import base64
import random
import secrets
from datetime import datetime, timedelta
from typing import Any, Literal

from gmail_multi_user.sandbox.mode import get_sandbox_config

# Sample data for generating realistic mock messages
SAMPLE_SENDERS = [
    ("Alice Johnson", "alice@example.com"),
    ("Bob Smith", "bob@company.com"),
    ("Carol Williams", "carol@business.org"),
    ("David Brown", "david@startup.io"),
    ("Eve Davis", "eve@corporate.net"),
    ("GitHub", "noreply@github.com"),
    ("Slack", "no-reply@slack.com"),
    ("Google", "noreply@google.com"),
]

SAMPLE_SUBJECTS = [
    "Meeting tomorrow at 2pm",
    "Project update - Q4 planning",
    "Quick question about the proposal",
    "Re: Follow up on our conversation",
    "Invitation: Weekly standup",
    "Your pull request was approved",
    "New comment on your document",
    "Reminder: Deadline approaching",
    "FW: Important announcement",
    "Invoice #12345",
    "Welcome to our service!",
    "Security alert: New sign-in",
]

SAMPLE_BODIES = [
    "Hi,\n\nJust wanted to follow up on our discussion from yesterday. Let me know when you have a chance to review.\n\nBest,\n",
    "Thanks for getting back to me. I've attached the updated document.\n\nCheers,\n",
    "The meeting has been moved to Thursday. Please update your calendar.\n\nRegards,\n",
    "I've reviewed your changes and they look great. Let's discuss next steps.\n\n",
    "Please see the attached report for your review. Let me know if you have any questions.\n\nThanks,\n",
    "This is a reminder that the deadline is next week. Please ensure all deliverables are ready.\n\n",
]

SAMPLE_LABELS = [
    {"id": "INBOX", "name": "INBOX", "type": "system"},
    {"id": "SENT", "name": "SENT", "type": "system"},
    {"id": "DRAFT", "name": "DRAFT", "type": "system"},
    {"id": "TRASH", "name": "TRASH", "type": "system"},
    {"id": "SPAM", "name": "SPAM", "type": "system"},
    {"id": "STARRED", "name": "STARRED", "type": "system"},
    {"id": "UNREAD", "name": "UNREAD", "type": "system"},
    {"id": "IMPORTANT", "name": "IMPORTANT", "type": "system"},
    {"id": "Label_1", "name": "Work", "type": "user"},
    {"id": "Label_2", "name": "Personal", "type": "user"},
    {"id": "Label_3", "name": "Projects", "type": "user"},
]


class MockGmailAPIClient:
    """Mock Gmail API client for sandbox mode.

    Generates realistic mock Gmail data for testing.
    All operations complete successfully without real API calls.

    Example:
        client = MockGmailAPIClient()
        result = await client.search(token="fake", query="is:unread")
        messages = await client.batch_get_messages(token="fake", message_ids=["msg1"])
    """

    def __init__(self, http_client: Any = None) -> None:
        """Initialize mock Gmail client.

        Args:
            http_client: HTTP client (ignored in mock).
        """
        self._sandbox_config = get_sandbox_config()
        self._messages: dict[str, dict] = {}
        self._threads: dict[str, list[str]] = {}
        self._drafts: dict[str, dict] = {}
        self._generate_sample_data()

    def _generate_sample_data(self) -> None:
        """Generate sample messages and threads."""
        config = self._sandbox_config
        thread_count = config.thread_count
        messages_per_thread = config.message_count // thread_count

        for _i in range(thread_count):
            thread_id = f"thread_{secrets.token_hex(8)}"
            thread_messages = []

            # Generate messages in this thread
            for j in range(messages_per_thread):
                msg_id = f"msg_{secrets.token_hex(8)}"
                sender_name, sender_email = random.choice(SAMPLE_SENDERS)
                subject = random.choice(SAMPLE_SUBJECTS)
                body = random.choice(SAMPLE_BODIES) + sender_name
                date = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

                labels = ["INBOX"]
                if random.random() < 0.3:
                    labels.append("UNREAD")
                if random.random() < 0.1:
                    labels.append("STARRED")
                if random.random() < 0.2:
                    labels.append(random.choice(["Label_1", "Label_2", "Label_3"]))

                self._messages[msg_id] = {
                    "id": msg_id,
                    "threadId": thread_id,
                    "labelIds": labels,
                    "snippet": body[:100],
                    "internalDate": str(int(date.timestamp() * 1000)),
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [
                            {"name": "Subject", "value": subject if j == 0 else f"Re: {subject}"},
                            {"name": "From", "value": f"{sender_name} <{sender_email}>"},
                            {"name": "To", "value": config.default_user_email},
                            {"name": "Date", "value": date.strftime("%a, %d %b %Y %H:%M:%S +0000")},
                            {"name": "Message-ID", "value": f"<{msg_id}@sandbox.example.com>"},
                        ],
                        "body": {
                            "size": len(body),
                            "data": base64.urlsafe_b64encode(body.encode()).decode(),
                        },
                    },
                }
                thread_messages.append(msg_id)

            self._threads[thread_id] = thread_messages

    async def close(self) -> None:
        """Close resources (no-op for mock)."""
        pass

    async def search(
        self,
        token: str,
        query: str,
        max_results: int = 10,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """Search for messages.

        Args:
            token: Access token (ignored).
            query: Search query.
            max_results: Maximum results.
            page_token: Pagination token.

        Returns:
            Search results with message IDs.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        # Simple query matching
        matching = []
        for msg_id, msg in self._messages.items():
            include = True

            if "is:unread" in query.lower():
                include = "UNREAD" in msg["labelIds"]
            elif "is:starred" in query.lower():
                include = "STARRED" in msg["labelIds"]
            elif "in:inbox" in query.lower():
                include = "INBOX" in msg["labelIds"]

            if include:
                matching.append({"id": msg_id, "threadId": msg["threadId"]})

        # Apply pagination
        start = 0
        if page_token:
            try:
                start = int(page_token)
            except ValueError:
                pass

        results = matching[start:start + max_results]
        next_page = None
        if start + max_results < len(matching):
            next_page = str(start + max_results)

        return {
            "messages": results if results else None,
            "nextPageToken": next_page,
            "resultSizeEstimate": len(matching),
        }

    async def get_message(
        self,
        token: str,
        message_id: str,
        format: Literal["full", "metadata", "minimal"] = "full",
    ) -> dict[str, Any]:
        """Get a single message.

        Args:
            token: Access token (ignored).
            message_id: Message ID.
            format: Response format.

        Returns:
            Message data.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        if message_id not in self._messages:
            raise Exception(f"Message not found: {message_id}")

        msg = self._messages[message_id].copy()

        if format == "minimal":
            return {
                "id": msg["id"],
                "threadId": msg["threadId"],
                "labelIds": msg["labelIds"],
            }
        elif format == "metadata":
            return {
                "id": msg["id"],
                "threadId": msg["threadId"],
                "labelIds": msg["labelIds"],
                "snippet": msg["snippet"],
                "payload": {
                    "headers": msg["payload"]["headers"],
                },
            }

        return msg

    async def batch_get_messages(
        self,
        token: str,
        message_ids: list[str],
        format: Literal["full", "metadata", "minimal"] = "metadata",
    ) -> list[dict[str, Any]]:
        """Get multiple messages.

        Args:
            token: Access token (ignored).
            message_ids: List of message IDs.
            format: Response format.

        Returns:
            List of message data.
        """
        results = []
        for msg_id in message_ids:
            try:
                msg = await self.get_message(token, msg_id, format)
                results.append(msg)
            except Exception:
                continue
        return results

    async def get_thread(
        self,
        token: str,
        thread_id: str,
        format: Literal["full", "metadata", "minimal"] = "full",
    ) -> dict[str, Any]:
        """Get a thread with all messages.

        Args:
            token: Access token (ignored).
            thread_id: Thread ID.
            format: Response format.

        Returns:
            Thread data with messages.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        if thread_id not in self._threads:
            raise Exception(f"Thread not found: {thread_id}")

        message_ids = self._threads[thread_id]
        messages = await self.batch_get_messages(token, message_ids, format)

        return {
            "id": thread_id,
            "historyId": secrets.token_hex(8),
            "messages": messages,
        }

    async def list_labels(self, token: str) -> dict[str, Any]:
        """List all labels.

        Args:
            token: Access token (ignored).

        Returns:
            Labels list.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        return {"labels": SAMPLE_LABELS}

    async def get_attachment(
        self,
        token: str,
        message_id: str,
        attachment_id: str,
    ) -> dict[str, Any]:
        """Get attachment data.

        Args:
            token: Access token (ignored).
            message_id: Message ID.
            attachment_id: Attachment ID.

        Returns:
            Attachment data (mock).
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        # Return mock attachment data
        mock_content = b"This is mock attachment content for sandbox testing."
        return {
            "size": len(mock_content),
            "data": base64.urlsafe_b64encode(mock_content).decode(),
        }

    async def get_profile(self, token: str) -> dict[str, Any]:
        """Get Gmail profile.

        Args:
            token: Access token (ignored).

        Returns:
            Profile data.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        return {
            "emailAddress": self._sandbox_config.default_user_email,
            "messagesTotal": len(self._messages),
            "threadsTotal": len(self._threads),
            "historyId": secrets.token_hex(8),
        }

    async def send_message(
        self,
        token: str,
        raw_message: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a message.

        Args:
            token: Access token (ignored).
            raw_message: Base64 encoded message.
            thread_id: Thread to reply to.

        Returns:
            Sent message info.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        msg_id = f"msg_{secrets.token_hex(8)}"
        tid = thread_id or f"thread_{secrets.token_hex(8)}"

        return {
            "id": msg_id,
            "threadId": tid,
            "labelIds": ["SENT"],
        }

    async def create_draft(
        self,
        token: str,
        raw_message: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a draft.

        Args:
            token: Access token (ignored).
            raw_message: Base64 encoded message.
            thread_id: Thread for reply draft.

        Returns:
            Draft info.
        """
        import asyncio
        await asyncio.sleep(self._sandbox_config.latency_ms / 1000)

        draft_id = f"draft_{secrets.token_hex(8)}"
        msg_id = f"msg_{secrets.token_hex(8)}"

        self._drafts[draft_id] = {
            "id": draft_id,
            "message": {
                "id": msg_id,
                "threadId": thread_id or f"thread_{secrets.token_hex(8)}",
                "labelIds": ["DRAFT"],
            },
        }

        return self._drafts[draft_id]

    async def update_draft(
        self,
        token: str,
        draft_id: str,
        raw_message: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Update a draft.

        Args:
            token: Access token (ignored).
            draft_id: Draft to update.
            raw_message: New message content.
            thread_id: Thread for reply.

        Returns:
            Updated draft info.
        """
        if draft_id not in self._drafts:
            raise Exception(f"Draft not found: {draft_id}")

        # Update draft (in sandbox, just return same structure)
        return self._drafts[draft_id]

    async def send_draft(
        self,
        token: str,
        draft_id: str,
    ) -> dict[str, Any]:
        """Send a draft.

        Args:
            token: Access token (ignored).
            draft_id: Draft to send.

        Returns:
            Sent message info.
        """
        if draft_id not in self._drafts:
            raise Exception(f"Draft not found: {draft_id}")

        draft = self._drafts.pop(draft_id)
        return {
            "id": draft["message"]["id"],
            "threadId": draft["message"]["threadId"],
            "labelIds": ["SENT"],
        }

    async def delete_draft(
        self,
        token: str,
        draft_id: str,
    ) -> None:
        """Delete a draft.

        Args:
            token: Access token (ignored).
            draft_id: Draft to delete.
        """
        if draft_id in self._drafts:
            del self._drafts[draft_id]

    async def list_drafts(self, token: str) -> dict[str, Any]:
        """List drafts.

        Args:
            token: Access token (ignored).

        Returns:
            List of drafts.
        """
        return {
            "drafts": [
                {"id": d["id"], "message": {"id": d["message"]["id"]}}
                for d in self._drafts.values()
            ]
        }

    async def modify_message_labels(
        self,
        token: str,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Modify message labels.

        Args:
            token: Access token (ignored).
            message_id: Message to modify.
            add_labels: Labels to add.
            remove_labels: Labels to remove.

        Returns:
            Updated message.
        """
        if message_id not in self._messages:
            raise Exception(f"Message not found: {message_id}")

        msg = self._messages[message_id]
        labels = set(msg["labelIds"])

        if add_labels:
            labels.update(add_labels)
        if remove_labels:
            labels -= set(remove_labels)

        msg["labelIds"] = list(labels)
        return msg

    async def batch_modify_labels(
        self,
        token: str,
        message_ids: list[str],
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> None:
        """Batch modify labels.

        Args:
            token: Access token (ignored).
            message_ids: Messages to modify.
            add_labels: Labels to add.
            remove_labels: Labels to remove.
        """
        for msg_id in message_ids:
            try:
                await self.modify_message_labels(token, msg_id, add_labels, remove_labels)
            except Exception:
                continue

    async def trash_message(
        self,
        token: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Move message to trash.

        Args:
            token: Access token (ignored).
            message_id: Message to trash.

        Returns:
            Updated message.
        """
        return await self.modify_message_labels(
            token, message_id, add_labels=["TRASH"], remove_labels=["INBOX"]
        )

    async def untrash_message(
        self,
        token: str,
        message_id: str,
    ) -> dict[str, Any]:
        """Remove message from trash.

        Args:
            token: Access token (ignored).
            message_id: Message to untrash.

        Returns:
            Updated message.
        """
        return await self.modify_message_labels(
            token, message_id, add_labels=["INBOX"], remove_labels=["TRASH"]
        )
