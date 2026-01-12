"""Tests for GmailService."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gmail_multi_user.service import GmailService
from gmail_multi_user.types import Message, Contact, Attachment


@pytest.fixture
def mock_config():
    """Create mock config."""
    config = MagicMock()
    config.token_refresh_buffer_seconds = 300
    return config


@pytest.fixture
def mock_storage():
    """Create mock storage backend."""
    return AsyncMock()


@pytest.fixture
def mock_token_manager():
    """Create mock token manager."""
    manager = AsyncMock()
    manager.get_valid_token = AsyncMock(return_value=MagicMock(access_token="test_token"))
    return manager


@pytest.fixture
def mock_api_client():
    """Create mock Gmail API client."""
    return AsyncMock()


@pytest.fixture
def service(mock_config, mock_storage, mock_token_manager, mock_api_client):
    """Create GmailService with mocked dependencies."""
    svc = GmailService(mock_config, mock_storage, mock_token_manager)
    svc._api_client = mock_api_client
    return svc


class TestGmailServiceSearch:
    """Tests for search operations."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self, service, mock_api_client, mock_storage):
        """Test successful search returns messages."""
        mock_api_client.search.return_value = {
            "messages": [
                {"id": "msg1", "threadId": "thread1"},
                {"id": "msg2", "threadId": "thread2"},
            ],
            "nextPageToken": "token123",
            "resultSizeEstimate": 100,
        }
        mock_api_client.batch_get_messages.return_value = [
            {
                "id": "msg1",
                "threadId": "thread1",
                "labelIds": ["INBOX"],
                "snippet": "Test snippet",
                "payload": {"headers": [{"name": "Subject", "value": "Test"}]},
            },
            {
                "id": "msg2",
                "threadId": "thread2",
                "labelIds": ["INBOX"],
                "snippet": "Test snippet 2",
                "payload": {"headers": [{"name": "Subject", "value": "Test 2"}]},
            },
        ]

        result = await service.search("conn_123", query="is:unread", max_results=10)

        assert len(result.messages) == 2
        assert result.next_page_token == "token123"
        assert result.total_estimate == 100
        mock_storage.update_connection_last_used.assert_called_once_with("conn_123")

    @pytest.mark.asyncio
    async def test_search_empty_results(self, service, mock_api_client, mock_storage):
        """Test search with no results."""
        mock_api_client.search.return_value = {
            "resultSizeEstimate": 0,
        }

        result = await service.search("conn_123", query="nonexistent")

        assert len(result.messages) == 0
        assert result.total_estimate == 0

    @pytest.mark.asyncio
    async def test_search_with_body(self, service, mock_api_client):
        """Test search with include_body=True."""
        mock_api_client.search.return_value = {
            "messages": [{"id": "msg1", "threadId": "thread1"}],
            "resultSizeEstimate": 1,
        }
        mock_api_client.batch_get_messages.return_value = [
            {
                "id": "msg1",
                "threadId": "thread1",
                "labelIds": ["INBOX"],
                "snippet": "Test",
                "payload": {
                    "mimeType": "text/plain",
                    "headers": [{"name": "Subject", "value": "Test"}],
                    "body": {"data": "SGVsbG8="},  # "Hello" in base64
                },
            },
        ]

        await service.search("conn_123", query="test", include_body=True)

        mock_api_client.batch_get_messages.assert_called_once()
        call_args = mock_api_client.batch_get_messages.call_args
        assert call_args.kwargs["format"] == "full"


class TestGmailServiceMessage:
    """Tests for message operations."""

    @pytest.mark.asyncio
    async def test_get_message_full(self, service, mock_api_client, mock_storage):
        """Test getting full message."""
        mock_api_client.get_message.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Test snippet",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "body": {"data": "SGVsbG8="},
            },
        }

        message = await service.get_message("conn_123", "msg123", format="full")

        assert message.id == "msg123"
        assert message.thread_id == "thread123"
        mock_storage.update_connection_last_used.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_metadata(self, service, mock_api_client):
        """Test getting message metadata only."""
        mock_api_client.get_message.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": ["INBOX"],
            "snippet": "Test",
            "payload": {
                "headers": [{"name": "Subject", "value": "Test"}],
            },
        }

        message = await service.get_message("conn_123", "msg123", format="metadata")

        assert message.id == "msg123"

    @pytest.mark.asyncio
    async def test_batch_get_messages(self, service, mock_api_client):
        """Test batch getting messages."""
        mock_api_client.batch_get_messages.return_value = [
            {"id": "msg1", "threadId": "t1", "labelIds": ["INBOX"], "payload": {"headers": []}},
            {"id": "msg2", "threadId": "t2", "labelIds": ["INBOX"], "payload": {"headers": []}},
        ]

        messages = await service.batch_get_messages("conn_123", ["msg1", "msg2"])

        assert len(messages) == 2


class TestGmailServiceThread:
    """Tests for thread operations."""

    @pytest.mark.asyncio
    async def test_get_thread(self, service, mock_api_client, mock_storage):
        """Test getting a thread."""
        mock_api_client.get_thread.return_value = {
            "id": "thread123",
            "historyId": "12345",
            "messages": [
                {
                    "id": "msg1",
                    "threadId": "thread123",
                    "labelIds": ["INBOX"],
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [{"name": "Subject", "value": "Thread Subject"}],
                        "body": {"data": "SGVsbG8="},
                    },
                },
                {
                    "id": "msg2",
                    "threadId": "thread123",
                    "labelIds": ["INBOX"],
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [{"name": "Subject", "value": "Re: Thread Subject"}],
                        "body": {"data": "V29ybGQ="},
                    },
                },
            ],
        }

        thread = await service.get_thread("conn_123", "thread123")

        assert thread.id == "thread123"
        assert thread.message_count == 2
        assert len(thread.messages) == 2
        assert thread.subject == "Thread Subject"


class TestGmailServiceLabels:
    """Tests for label operations."""

    @pytest.mark.asyncio
    async def test_list_labels(self, service, mock_api_client):
        """Test listing labels."""
        mock_api_client.list_labels.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "Label_1", "name": "Work", "type": "user"},
            ],
        }

        labels = await service.list_labels("conn_123")

        assert len(labels) == 2
        assert labels[0].id == "INBOX"
        assert labels[0].type == "system"
        assert labels[1].name == "Work"
        assert labels[1].type == "user"

    @pytest.mark.asyncio
    async def test_modify_labels(self, service, mock_api_client):
        """Test modifying message labels."""
        mock_api_client.modify_message_labels.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": ["INBOX", "STARRED"],
        }

        result = await service.modify_labels(
            "conn_123",
            "msg123",
            add_labels=["STARRED"],
            remove_labels=["UNREAD"],
        )

        assert "STARRED" in result.labels

    @pytest.mark.asyncio
    async def test_batch_modify_labels(self, service, mock_api_client):
        """Test batch label modification."""
        await service.batch_modify_labels(
            "conn_123",
            ["msg1", "msg2", "msg3"],
            add_labels=["STARRED"],
        )

        mock_api_client.batch_modify_labels.assert_called_once()

    @pytest.mark.asyncio
    async def test_archive(self, service, mock_api_client):
        """Test archiving a message."""
        mock_api_client.modify_message_labels.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": [],
        }

        await service.archive("conn_123", "msg123")

        mock_api_client.modify_message_labels.assert_called_once()
        call_args = mock_api_client.modify_message_labels.call_args
        assert "INBOX" in call_args.kwargs["remove_labels"]

    @pytest.mark.asyncio
    async def test_mark_read(self, service, mock_api_client):
        """Test marking messages as read."""
        mock_api_client.modify_message_labels.return_value = {
            "id": "msg123",
            "labelIds": ["INBOX"],
        }

        await service.mark_read("conn_123", ["msg123"])

        mock_api_client.modify_message_labels.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_read_batch(self, service, mock_api_client):
        """Test marking multiple messages as read uses batch."""
        await service.mark_read("conn_123", ["msg1", "msg2", "msg3"])

        mock_api_client.batch_modify_labels.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_unread(self, service, mock_api_client):
        """Test marking messages as unread."""
        mock_api_client.modify_message_labels.return_value = {
            "id": "msg123",
            "labelIds": ["INBOX", "UNREAD"],
        }

        await service.mark_unread("conn_123", ["msg123"])

        mock_api_client.modify_message_labels.assert_called_once()


class TestGmailServiceTrash:
    """Tests for trash operations."""

    @pytest.mark.asyncio
    async def test_trash(self, service, mock_api_client):
        """Test trashing a message."""
        mock_api_client.trash_message.return_value = {
            "id": "msg123",
            "labelIds": ["TRASH"],
        }

        result = await service.trash("conn_123", "msg123")

        mock_api_client.trash_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_untrash(self, service, mock_api_client):
        """Test untrashing a message."""
        mock_api_client.untrash_message.return_value = {
            "id": "msg123",
            "labelIds": ["INBOX"],
        }

        result = await service.untrash("conn_123", "msg123")

        mock_api_client.untrash_message.assert_called_once()


class TestGmailServiceSend:
    """Tests for send operations."""

    @pytest.mark.asyncio
    async def test_send(self, service, mock_api_client):
        """Test sending a message."""
        mock_api_client.send_message.return_value = {
            "id": "sent_msg_123",
            "threadId": "new_thread_123",
            "labelIds": ["SENT"],
        }

        result = await service.send(
            "conn_123",
            to=["recipient@example.com"],
            subject="Test Subject",
            body="Test body",
        )

        assert result.success is True
        assert result.message_id == "sent_msg_123"
        assert result.thread_id == "new_thread_123"

    @pytest.mark.asyncio
    async def test_send_with_html(self, service, mock_api_client):
        """Test sending HTML email."""
        mock_api_client.send_message.return_value = {
            "id": "msg123",
            "threadId": "thread123",
        }

        await service.send(
            "conn_123",
            to=["recipient@example.com"],
            subject="HTML Test",
            body="Plain text",
            body_html="<h1>HTML content</h1>",
        )

        mock_api_client.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_reply(self, service, mock_api_client):
        """Test replying to a message."""
        # Mock get_message for fetching original
        mock_api_client.get_message.return_value = {
            "id": "original_msg",
            "threadId": "thread123",
            "labelIds": ["INBOX"],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Original Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "me@example.com"},
                    {"name": "Message-ID", "value": "<original@example.com>"},
                ],
                "body": {"data": "T3JpZ2luYWw="},
            },
        }
        mock_api_client.send_message.return_value = {
            "id": "reply_msg",
            "threadId": "thread123",
        }

        result = await service.reply(
            "conn_123",
            message_id="original_msg",
            body="This is my reply",
        )

        assert result.success is True
        assert result.thread_id == "thread123"


class TestGmailServiceDraft:
    """Tests for draft operations."""

    @pytest.mark.asyncio
    async def test_create_draft(self, service, mock_api_client):
        """Test creating a draft."""
        mock_api_client.create_draft.return_value = {
            "id": "draft123",
            "message": {
                "id": "msg123",
                "threadId": "thread123",
            },
        }

        result = await service.create_draft(
            "conn_123",
            to=["recipient@example.com"],
            subject="Draft Subject",
            body="Draft body",
        )

        assert result.draft_id == "draft123"
        assert result.message_id == "msg123"

    @pytest.mark.asyncio
    async def test_update_draft(self, service, mock_api_client):
        """Test updating a draft."""
        mock_api_client.update_draft.return_value = {
            "id": "draft123",
            "message": {
                "id": "msg123",
            },
        }

        result = await service.update_draft(
            "conn_123",
            draft_id="draft123",
            to=["new@example.com"],
            subject="Updated Subject",
            body="Updated body",
        )

        assert result.draft_id == "draft123"

    @pytest.mark.asyncio
    async def test_send_draft(self, service, mock_api_client):
        """Test sending a draft."""
        mock_api_client.send_draft.return_value = {
            "id": "sent_msg",
            "threadId": "thread123",
            "labelIds": ["SENT"],
        }

        result = await service.send_draft("conn_123", "draft123")

        assert result.success is True
        assert result.message_id == "sent_msg"

    @pytest.mark.asyncio
    async def test_delete_draft(self, service, mock_api_client):
        """Test deleting a draft."""
        await service.delete_draft("conn_123", "draft123")

        mock_api_client.delete_draft.assert_called_once_with(
            token="test_token",
            draft_id="draft123",
        )


class TestGmailServiceProfile:
    """Tests for profile operations."""

    @pytest.mark.asyncio
    async def test_get_profile(self, service, mock_api_client):
        """Test getting profile."""
        mock_api_client.get_profile.return_value = {
            "emailAddress": "user@gmail.com",
            "messagesTotal": 5000,
            "threadsTotal": 2500,
            "historyId": "123456",
        }

        profile = await service.get_profile("conn_123")

        assert profile["email_address"] == "user@gmail.com"
        assert profile["messages_total"] == 5000
        assert profile["threads_total"] == 2500


class TestGmailServiceAttachment:
    """Tests for attachment operations."""

    @pytest.mark.asyncio
    async def test_get_attachment(self, service, mock_api_client):
        """Test getting an attachment."""
        # Mock the message to get attachment metadata
        mock_api_client.get_message.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": ["INBOX"],
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [{"name": "Subject", "value": "With Attachment"}],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": "VGV4dA=="},
                    },
                    {
                        "filename": "test.pdf",
                        "mimeType": "application/pdf",
                        "body": {"attachmentId": "att123", "size": 1024},
                    },
                ],
            },
        }
        mock_api_client.get_attachment.return_value = {
            "size": 1024,
            "data": "UERGIGNvbnRlbnQ=",  # "PDF content" in base64
        }

        attachment = await service.get_attachment("conn_123", "msg123", "att123")

        assert attachment.filename == "test.pdf"
        assert attachment.mime_type == "application/pdf"
        assert attachment.size == 1024


class TestGmailServiceClose:
    """Tests for resource cleanup."""

    @pytest.mark.asyncio
    async def test_close(self, service, mock_api_client):
        """Test closing service resources."""
        await service.close()

        mock_api_client.close.assert_called_once()
