"""Unit tests for Gmail API client write operations."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from gmail_multi_user.gmail.client import GmailAPIClient


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Create a mock HTTP client."""
    return MagicMock(spec=httpx.AsyncClient)


@pytest.fixture
def api_client(mock_http_client: MagicMock) -> GmailAPIClient:
    """Create an API client with mock HTTP client."""
    return GmailAPIClient(http_client=mock_http_client)


def create_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
) -> MagicMock:
    """Create a mock HTTP response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {}
    return response


class TestSendMessage:
    """Tests for send_message method."""

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test sending a message successfully."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "id": "msg123",
                    "threadId": "thread456",
                    "labelIds": ["SENT"],
                },
            )
        )

        result = await api_client.send_message(
            token="test_token",
            raw_message="base64encoded",
        )

        assert result["id"] == "msg123"
        assert result["threadId"] == "thread456"

        mock_http_client.request.assert_called_once()
        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/messages/send" in call_kwargs["url"]
        assert call_kwargs["json"]["raw"] == "base64encoded"

    @pytest.mark.asyncio
    async def test_send_message_with_thread_id(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test sending a message in a thread."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {"id": "msg123", "threadId": "thread456"},
            )
        )

        result = await api_client.send_message(
            token="test_token",
            raw_message="base64encoded",
            thread_id="thread456",
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["json"]["threadId"] == "thread456"


class TestDraftOperations:
    """Tests for draft operations."""

    @pytest.mark.asyncio
    async def test_create_draft(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test creating a draft."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "id": "draft123",
                    "message": {
                        "id": "msg456",
                        "threadId": "thread789",
                    },
                },
            )
        )

        result = await api_client.create_draft(
            token="test_token",
            raw_message="base64encoded",
        )

        assert result["id"] == "draft123"
        assert result["message"]["id"] == "msg456"

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/drafts" in call_kwargs["url"]
        assert call_kwargs["json"]["message"]["raw"] == "base64encoded"

    @pytest.mark.asyncio
    async def test_create_draft_with_thread_id(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test creating a draft in a thread."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(200, {"id": "draft123"})
        )

        await api_client.create_draft(
            token="test_token",
            raw_message="base64encoded",
            thread_id="thread456",
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["json"]["message"]["threadId"] == "thread456"

    @pytest.mark.asyncio
    async def test_get_draft(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test getting a draft."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "id": "draft123",
                    "message": {"id": "msg456"},
                },
            )
        )

        result = await api_client.get_draft(
            token="test_token",
            draft_id="draft123",
        )

        assert result["id"] == "draft123"

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "GET"
        assert "/drafts/draft123" in call_kwargs["url"]

    @pytest.mark.asyncio
    async def test_update_draft(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test updating a draft."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(200, {"id": "draft123"})
        )

        result = await api_client.update_draft(
            token="test_token",
            draft_id="draft123",
            raw_message="updated_base64",
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "PUT"
        assert "/drafts/draft123" in call_kwargs["url"]
        assert call_kwargs["json"]["message"]["raw"] == "updated_base64"

    @pytest.mark.asyncio
    async def test_send_draft(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test sending a draft."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {"id": "msg123", "threadId": "thread456"},
            )
        )

        result = await api_client.send_draft(
            token="test_token",
            draft_id="draft123",
        )

        assert result["id"] == "msg123"

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/drafts/send" in call_kwargs["url"]
        assert call_kwargs["json"]["id"] == "draft123"

    @pytest.mark.asyncio
    async def test_delete_draft(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test deleting a draft."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(204)
        )

        result = await api_client.delete_draft(
            token="test_token",
            draft_id="draft123",
        )

        assert result == {}

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "DELETE"
        assert "/drafts/draft123" in call_kwargs["url"]

    @pytest.mark.asyncio
    async def test_list_drafts(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test listing drafts."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "drafts": [
                        {"id": "draft1"},
                        {"id": "draft2"},
                    ],
                    "nextPageToken": "token123",
                },
            )
        )

        result = await api_client.list_drafts(
            token="test_token",
            max_results=10,
        )

        assert len(result["drafts"]) == 2
        assert result["nextPageToken"] == "token123"


class TestLabelModification:
    """Tests for label modification operations."""

    @pytest.mark.asyncio
    async def test_modify_message_labels(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test modifying labels on a message."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "id": "msg123",
                    "threadId": "thread456",
                    "labelIds": ["INBOX", "STARRED"],
                },
            )
        )

        result = await api_client.modify_message_labels(
            token="test_token",
            message_id="msg123",
            add_labels=["STARRED"],
            remove_labels=["UNREAD"],
        )

        assert "STARRED" in result["labelIds"]

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/messages/msg123/modify" in call_kwargs["url"]
        assert call_kwargs["json"]["addLabelIds"] == ["STARRED"]
        assert call_kwargs["json"]["removeLabelIds"] == ["UNREAD"]

    @pytest.mark.asyncio
    async def test_modify_message_labels_add_only(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test adding labels only."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(200, {"id": "msg123"})
        )

        await api_client.modify_message_labels(
            token="test_token",
            message_id="msg123",
            add_labels=["IMPORTANT"],
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert "addLabelIds" in call_kwargs["json"]
        assert "removeLabelIds" not in call_kwargs["json"]

    @pytest.mark.asyncio
    async def test_batch_modify_labels(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test batch modifying labels."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(204)
        )

        result = await api_client.batch_modify_labels(
            token="test_token",
            message_ids=["msg1", "msg2", "msg3"],
            add_labels=["STARRED"],
            remove_labels=["UNREAD"],
        )

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/messages/batchModify" in call_kwargs["url"]
        assert call_kwargs["json"]["ids"] == ["msg1", "msg2", "msg3"]


class TestTrashOperations:
    """Tests for trash operations."""

    @pytest.mark.asyncio
    async def test_trash_message(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test moving a message to trash."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "id": "msg123",
                    "labelIds": ["TRASH"],
                },
            )
        )

        result = await api_client.trash_message(
            token="test_token",
            message_id="msg123",
        )

        assert "TRASH" in result["labelIds"]

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/messages/msg123/trash" in call_kwargs["url"]

    @pytest.mark.asyncio
    async def test_untrash_message(
        self,
        api_client: GmailAPIClient,
        mock_http_client: MagicMock,
    ) -> None:
        """Test removing a message from trash."""
        mock_http_client.request = AsyncMock(
            return_value=create_response(
                200,
                {
                    "id": "msg123",
                    "labelIds": ["INBOX"],
                },
            )
        )

        result = await api_client.untrash_message(
            token="test_token",
            message_id="msg123",
        )

        assert "TRASH" not in result["labelIds"]

        call_kwargs = mock_http_client.request.call_args[1]
        assert call_kwargs["method"] == "POST"
        assert "/messages/msg123/untrash" in call_kwargs["url"]
