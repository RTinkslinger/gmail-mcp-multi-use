"""Unit tests for GmailService write operations."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from gmail_multi_user.service import GmailService
from gmail_multi_user.tokens import ValidToken
from gmail_multi_user.types import (
    AttachmentInput,
    DraftResult,
    SendResult,
)


@pytest.fixture
def mock_config() -> MagicMock:
    """Create a mock config."""
    return MagicMock()


@pytest.fixture
def mock_storage() -> MagicMock:
    """Create a mock storage backend."""
    storage = MagicMock()
    storage.update_connection_last_used = AsyncMock()
    return storage


@pytest.fixture
def mock_token_manager() -> MagicMock:
    """Create a mock token manager."""
    manager = MagicMock()
    manager.get_valid_token = AsyncMock(
        return_value=ValidToken(
            access_token="test_access_token",
            expires_at=datetime.now() + timedelta(hours=1),
            connection_id="conn123",
            gmail_address="test@example.com",
        )
    )
    return manager


@pytest.fixture
def service(
    mock_config: MagicMock,
    mock_storage: MagicMock,
    mock_token_manager: MagicMock,
) -> GmailService:
    """Create a GmailService with mocked dependencies."""
    return GmailService(
        config=mock_config,
        storage=mock_storage,
        token_manager=mock_token_manager,
    )


class TestSendOperations:
    """Tests for send operations."""

    @pytest.mark.asyncio
    async def test_send_simple_email(
        self,
        service: GmailService,
        mock_storage: MagicMock,
    ) -> None:
        """Test sending a simple email."""
        service._api_client.send_message = AsyncMock(
            return_value={
                "id": "msg123",
                "threadId": "thread456",
                "labelIds": ["SENT"],
            }
        )

        result = await service.send(
            connection_id="conn123",
            to=["bob@example.com"],
            subject="Hello",
            body="Hi Bob!",
        )

        assert isinstance(result, SendResult)
        assert result.success is True
        assert result.message_id == "msg123"
        assert result.thread_id == "thread456"

        mock_storage.update_connection_last_used.assert_called_once_with("conn123")

    @pytest.mark.asyncio
    async def test_send_email_with_html(
        self,
        service: GmailService,
    ) -> None:
        """Test sending email with HTML body."""
        service._api_client.send_message = AsyncMock(
            return_value={"id": "msg123", "threadId": "thread456", "labelIds": []}
        )

        result = await service.send(
            connection_id="conn123",
            to=["bob@example.com"],
            subject="HTML Test",
            body="Plain text",
            body_html="<h1>HTML content</h1>",
        )

        assert result.message_id == "msg123"

    @pytest.mark.asyncio
    async def test_send_email_with_attachments(
        self,
        service: GmailService,
    ) -> None:
        """Test sending email with attachments."""
        service._api_client.send_message = AsyncMock(
            return_value={"id": "msg123", "threadId": "thread456", "labelIds": []}
        )

        attachment = AttachmentInput(
            filename="test.txt",
            mime_type="text/plain",
            content=b"Hello attachment!",
        )

        result = await service.send(
            connection_id="conn123",
            to=["bob@example.com"],
            subject="With Attachment",
            body="See attached",
            attachments=[attachment],
        )

        assert result.message_id == "msg123"

    @pytest.mark.asyncio
    async def test_reply_to_message(
        self,
        service: GmailService,
    ) -> None:
        """Test replying to a message."""
        # Mock get_message to return original message data
        service._api_client.get_message = AsyncMock(
            return_value={
                "id": "orig123",
                "threadId": "thread456",
                "labelIds": ["INBOX"],
                "snippet": "Original",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "alice@example.com"},
                        {"name": "To", "value": "bob@example.com"},
                        {"name": "Subject", "value": "Hello"},
                        {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                    ],
                    "mimeType": "text/plain",
                    "body": {"data": "T3JpZ2luYWwgYm9keQ=="},  # "Original body"
                },
            }
        )

        service._api_client.send_message = AsyncMock(
            return_value={
                "id": "reply123",
                "threadId": "thread456",
                "labelIds": ["SENT"],
            }
        )

        result = await service.reply(
            connection_id="conn123",
            message_id="orig123",
            body="Thanks for your message!",
        )

        assert result.message_id == "reply123"
        assert result.thread_id == "thread456"

        # Verify send was called with thread_id
        call_kwargs = service._api_client.send_message.call_args[1]
        assert call_kwargs["thread_id"] == "thread456"


class TestDraftOperations:
    """Tests for draft operations."""

    @pytest.mark.asyncio
    async def test_create_draft(
        self,
        service: GmailService,
        mock_storage: MagicMock,
    ) -> None:
        """Test creating a draft."""
        service._api_client.create_draft = AsyncMock(
            return_value={
                "id": "draft123",
                "message": {
                    "id": "msg456",
                    "threadId": "thread789",
                },
            }
        )

        result = await service.create_draft(
            connection_id="conn123",
            to=["bob@example.com"],
            subject="Draft Subject",
            body="Draft body",
        )

        assert isinstance(result, DraftResult)
        assert result.draft_id == "draft123"
        assert result.message_id == "msg456"

        mock_storage.update_connection_last_used.assert_called_once_with("conn123")

    @pytest.mark.asyncio
    async def test_update_draft(
        self,
        service: GmailService,
    ) -> None:
        """Test updating a draft."""
        service._api_client.update_draft = AsyncMock(
            return_value={
                "id": "draft123",
                "message": {
                    "id": "msg456",
                    "threadId": "thread789",
                },
            }
        )

        result = await service.update_draft(
            connection_id="conn123",
            draft_id="draft123",
            to=["bob@example.com"],
            subject="Updated Subject",
            body="Updated body",
        )

        assert result.draft_id == "draft123"

    @pytest.mark.asyncio
    async def test_send_draft(
        self,
        service: GmailService,
    ) -> None:
        """Test sending a draft."""
        service._api_client.send_draft = AsyncMock(
            return_value={
                "id": "msg123",
                "threadId": "thread456",
                "labelIds": ["SENT"],
            }
        )

        result = await service.send_draft(
            connection_id="conn123",
            draft_id="draft123",
        )

        assert isinstance(result, SendResult)
        assert result.message_id == "msg123"

    @pytest.mark.asyncio
    async def test_delete_draft(
        self,
        service: GmailService,
        mock_storage: MagicMock,
    ) -> None:
        """Test deleting a draft."""
        service._api_client.delete_draft = AsyncMock(return_value={})

        await service.delete_draft(
            connection_id="conn123",
            draft_id="draft123",
        )

        service._api_client.delete_draft.assert_called_once_with(
            token="test_access_token",
            draft_id="draft123",
        )
        mock_storage.update_connection_last_used.assert_called_once()


class TestLabelOperations:
    """Tests for label modification operations."""

    @pytest.mark.asyncio
    async def test_modify_labels(
        self,
        service: GmailService,
    ) -> None:
        """Test modifying labels on a message."""
        service._api_client.modify_message_labels = AsyncMock(
            return_value={
                "id": "msg123",
                "threadId": "thread456",
                "labelIds": ["INBOX", "STARRED"],
            }
        )

        result = await service.modify_labels(
            connection_id="conn123",
            message_id="msg123",
            add_labels=["STARRED"],
            remove_labels=["UNREAD"],
        )

        assert result.id == "msg123"

        service._api_client.modify_message_labels.assert_called_once_with(
            token="test_access_token",
            message_id="msg123",
            add_labels=["STARRED"],
            remove_labels=["UNREAD"],
        )

    @pytest.mark.asyncio
    async def test_batch_modify_labels(
        self,
        service: GmailService,
        mock_storage: MagicMock,
    ) -> None:
        """Test batch modifying labels."""
        service._api_client.batch_modify_labels = AsyncMock(return_value={})

        await service.batch_modify_labels(
            connection_id="conn123",
            message_ids=["msg1", "msg2", "msg3"],
            add_labels=["STARRED"],
        )

        service._api_client.batch_modify_labels.assert_called_once_with(
            token="test_access_token",
            message_ids=["msg1", "msg2", "msg3"],
            add_labels=["STARRED"],
            remove_labels=None,
        )
        mock_storage.update_connection_last_used.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive(
        self,
        service: GmailService,
    ) -> None:
        """Test archiving a message."""
        service._api_client.modify_message_labels = AsyncMock(
            return_value={
                "id": "msg123",
                "threadId": "thread456",
                "labelIds": [],
            }
        )

        await service.archive(
            connection_id="conn123",
            message_id="msg123",
        )

        service._api_client.modify_message_labels.assert_called_once_with(
            token="test_access_token",
            message_id="msg123",
            add_labels=None,
            remove_labels=["INBOX"],
        )

    @pytest.mark.asyncio
    async def test_mark_read_single(
        self,
        service: GmailService,
    ) -> None:
        """Test marking a single message as read."""
        service._api_client.modify_message_labels = AsyncMock(
            return_value={"id": "msg123", "threadId": "t1", "labelIds": []}
        )

        await service.mark_read(
            connection_id="conn123",
            message_ids=["msg123"],
        )

        service._api_client.modify_message_labels.assert_called_once_with(
            token="test_access_token",
            message_id="msg123",
            add_labels=None,
            remove_labels=["UNREAD"],
        )

    @pytest.mark.asyncio
    async def test_mark_read_multiple(
        self,
        service: GmailService,
    ) -> None:
        """Test marking multiple messages as read."""
        service._api_client.batch_modify_labels = AsyncMock(return_value={})

        await service.mark_read(
            connection_id="conn123",
            message_ids=["msg1", "msg2", "msg3"],
        )

        service._api_client.batch_modify_labels.assert_called_once_with(
            token="test_access_token",
            message_ids=["msg1", "msg2", "msg3"],
            add_labels=None,
            remove_labels=["UNREAD"],
        )

    @pytest.mark.asyncio
    async def test_mark_unread_single(
        self,
        service: GmailService,
    ) -> None:
        """Test marking a single message as unread."""
        service._api_client.modify_message_labels = AsyncMock(
            return_value={"id": "msg123", "threadId": "t1", "labelIds": ["UNREAD"]}
        )

        await service.mark_unread(
            connection_id="conn123",
            message_ids=["msg123"],
        )

        service._api_client.modify_message_labels.assert_called_once_with(
            token="test_access_token",
            message_id="msg123",
            add_labels=["UNREAD"],
            remove_labels=None,
        )

    @pytest.mark.asyncio
    async def test_mark_unread_multiple(
        self,
        service: GmailService,
    ) -> None:
        """Test marking multiple messages as unread."""
        service._api_client.batch_modify_labels = AsyncMock(return_value={})

        await service.mark_unread(
            connection_id="conn123",
            message_ids=["msg1", "msg2"],
        )

        service._api_client.batch_modify_labels.assert_called_once_with(
            token="test_access_token",
            message_ids=["msg1", "msg2"],
            add_labels=["UNREAD"],
            remove_labels=None,
        )


class TestTrashOperations:
    """Tests for trash operations."""

    @pytest.mark.asyncio
    async def test_trash(
        self,
        service: GmailService,
        mock_storage: MagicMock,
    ) -> None:
        """Test moving a message to trash."""
        service._api_client.trash_message = AsyncMock(
            return_value={
                "id": "msg123",
                "threadId": "thread456",
                "labelIds": ["TRASH"],
            }
        )

        result = await service.trash(
            connection_id="conn123",
            message_id="msg123",
        )

        assert result.id == "msg123"

        service._api_client.trash_message.assert_called_once_with(
            token="test_access_token",
            message_id="msg123",
        )
        mock_storage.update_connection_last_used.assert_called_once()

    @pytest.mark.asyncio
    async def test_untrash(
        self,
        service: GmailService,
        mock_storage: MagicMock,
    ) -> None:
        """Test removing a message from trash."""
        service._api_client.untrash_message = AsyncMock(
            return_value={
                "id": "msg123",
                "threadId": "thread456",
                "labelIds": ["INBOX"],
            }
        )

        result = await service.untrash(
            connection_id="conn123",
            message_id="msg123",
        )

        assert result.id == "msg123"

        service._api_client.untrash_message.assert_called_once_with(
            token="test_access_token",
            message_id="msg123",
        )
        mock_storage.update_connection_last_used.assert_called_once()
