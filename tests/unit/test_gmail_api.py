"""Tests for Gmail API client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from gmail_multi_user.exceptions import GmailAPIError, RateLimitError, GMAIL_RATE_LIMIT
from gmail_multi_user.gmail.client import GmailAPIClient


class TestGmailAPIClient:
    """Tests for Gmail API client."""

    @pytest.fixture
    def mock_http_client(self):
        """Create a mock HTTP client."""
        return AsyncMock()

    @pytest.fixture
    def gmail_client(self, mock_http_client):
        """Create a Gmail API client with mock HTTP client."""
        return GmailAPIClient(http_client=mock_http_client)

    @pytest.mark.asyncio
    async def test_search_success(self, gmail_client, mock_http_client):
        """Test successful message search."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [
                {"id": "msg1", "threadId": "thread1"},
                {"id": "msg2", "threadId": "thread2"},
            ],
            "resultSizeEstimate": 100,
            "nextPageToken": "token123",
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.search(
            token="test_token",
            query="is:unread",
            max_results=10,
        )

        assert len(result["messages"]) == 2
        assert result["messages"][0]["id"] == "msg1"
        assert result["resultSizeEstimate"] == 100
        assert result["nextPageToken"] == "token123"

        # Verify request was made correctly
        mock_http_client.request.assert_called_once()
        call_args = mock_http_client.request.call_args
        assert call_args.kwargs["method"] == "GET"
        assert "messages" in call_args.kwargs["url"]
        assert "Bearer test_token" in call_args.kwargs["headers"]["Authorization"]
        assert call_args.kwargs["params"]["q"] == "is:unread"

    @pytest.mark.asyncio
    async def test_search_empty_results(self, gmail_client, mock_http_client):
        """Test search with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "resultSizeEstimate": 0,
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.search(
            token="test_token",
            query="nonexistent",
        )

        assert result.get("messages") is None
        assert result["resultSizeEstimate"] == 0

    @pytest.mark.asyncio
    async def test_search_with_pagination(self, gmail_client, mock_http_client):
        """Test search with pagination token."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": []}
        mock_http_client.request = AsyncMock(return_value=mock_response)

        await gmail_client.search(
            token="test_token",
            query="is:starred",
            page_token="next_page_token",
        )

        call_args = mock_http_client.request.call_args
        assert call_args.kwargs["params"]["pageToken"] == "next_page_token"

    @pytest.mark.asyncio
    async def test_get_message_full(self, gmail_client, mock_http_client):
        """Test getting full message."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "labelIds": ["INBOX", "UNREAD"],
            "snippet": "Test message snippet",
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                ],
                "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World" in base64
            },
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.get_message(
            token="test_token",
            message_id="msg123",
            format="full",
        )

        assert result["id"] == "msg123"
        assert result["threadId"] == "thread123"
        assert "payload" in result

    @pytest.mark.asyncio
    async def test_get_message_metadata(self, gmail_client, mock_http_client):
        """Test getting message metadata only."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Snippet",
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        await gmail_client.get_message(
            token="test_token",
            message_id="msg123",
            format="metadata",
        )

        call_args = mock_http_client.request.call_args
        assert call_args.kwargs["params"]["format"] == "metadata"

    @pytest.mark.asyncio
    async def test_get_thread(self, gmail_client, mock_http_client):
        """Test getting a thread."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "thread123",
            "historyId": "12345",
            "messages": [
                {"id": "msg1", "threadId": "thread123"},
                {"id": "msg2", "threadId": "thread123"},
            ],
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.get_thread(
            token="test_token",
            thread_id="thread123",
        )

        assert result["id"] == "thread123"
        assert len(result["messages"]) == 2

    @pytest.mark.asyncio
    async def test_list_labels(self, gmail_client, mock_http_client):
        """Test listing labels."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "Label_1", "name": "Work", "type": "user"},
            ],
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.list_labels(token="test_token")

        assert len(result["labels"]) == 2
        assert result["labels"][0]["id"] == "INBOX"
        assert result["labels"][1]["name"] == "Work"

    @pytest.mark.asyncio
    async def test_get_attachment(self, gmail_client, mock_http_client):
        """Test getting attachment data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "size": 1024,
            "data": "SGVsbG8gV29ybGQ=",  # base64url encoded
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.get_attachment(
            token="test_token",
            message_id="msg123",
            attachment_id="att456",
        )

        assert result["size"] == 1024
        assert "data" in result

    @pytest.mark.asyncio
    async def test_get_profile(self, gmail_client, mock_http_client):
        """Test getting profile."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "emailAddress": "user@gmail.com",
            "messagesTotal": 5000,
            "threadsTotal": 2500,
            "historyId": "123456",
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.get_profile(token="test_token")

        assert result["emailAddress"] == "user@gmail.com"
        assert result["messagesTotal"] == 5000

    @pytest.mark.asyncio
    async def test_rate_limit_error(self, gmail_client, mock_http_client):
        """Test rate limit handling."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_http_client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(RateLimitError) as exc_info:
            await gmail_client.search(token="test_token", query="is:unread")

        assert exc_info.value.code == GMAIL_RATE_LIMIT

    @pytest.mark.asyncio
    async def test_unauthorized_error(self, gmail_client, mock_http_client):
        """Test unauthorized error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": {
                "code": 401,
                "message": "Invalid Credentials",
            }
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(GmailAPIError) as exc_info:
            await gmail_client.get_message(token="bad_token", message_id="msg1")

        assert exc_info.value.code == "unauthorized"

    @pytest.mark.asyncio
    async def test_not_found_error(self, gmail_client, mock_http_client):
        """Test not found error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "error": {
                "code": 404,
                "message": "Requested entity was not found.",
            }
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(GmailAPIError) as exc_info:
            await gmail_client.get_message(token="test_token", message_id="nonexistent")

        assert exc_info.value.code == "not_found"

    @pytest.mark.asyncio
    async def test_permission_denied_error(self, gmail_client, mock_http_client):
        """Test permission denied error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "error": {
                "code": 403,
                "message": "Insufficient Permission",
            }
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        with pytest.raises(GmailAPIError) as exc_info:
            await gmail_client.list_labels(token="test_token")

        assert exc_info.value.code == "permission_denied"

    @pytest.mark.asyncio
    async def test_batch_get_messages(self, gmail_client, mock_http_client):
        """Test batch getting multiple messages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "msg1",
            "threadId": "thread1",
            "snippet": "Test",
        }
        mock_http_client.request = AsyncMock(return_value=mock_response)

        result = await gmail_client.batch_get_messages(
            token="test_token",
            message_ids=["msg1", "msg2", "msg3"],
            format="metadata",
        )

        assert len(result) == 3
        # Should be called 3 times (once per message)
        assert mock_http_client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_get_messages_handles_not_found(
        self, gmail_client, mock_http_client
    ):
        """Test batch get skips not found messages."""
        # First call succeeds, second returns 404, third succeeds
        mock_success = MagicMock()
        mock_success.status_code = 200
        mock_success.json.return_value = {"id": "msg1", "snippet": "Test"}

        mock_not_found = MagicMock()
        mock_not_found.status_code = 404
        mock_not_found.json.return_value = {"error": {"code": 404}}

        mock_http_client.request = AsyncMock(
            side_effect=[mock_success, mock_not_found, mock_success]
        )

        result = await gmail_client.batch_get_messages(
            token="test_token",
            message_ids=["msg1", "msg2", "msg3"],
        )

        # Only 2 messages should be returned (one was 404)
        assert len(result) == 2
