"""Tests for sandbox mode functionality."""

from __future__ import annotations

import os

import pytest

from gmail_multi_user.sandbox import (
    MockGmailAPIClient,
    MockGoogleOAuthClient,
    SandboxConfig,
    disable_sandbox_mode,
    enable_sandbox_mode,
    get_sandbox_config,
    is_sandbox_mode,
)


class TestSandboxMode:
    """Tests for sandbox mode state management."""

    def setup_method(self):
        """Reset sandbox state before each test."""
        disable_sandbox_mode()
        if "GMAIL_MCP_SANDBOX" in os.environ:
            del os.environ["GMAIL_MCP_SANDBOX"]

    def test_sandbox_disabled_by_default(self):
        """Test that sandbox is disabled by default."""
        assert is_sandbox_mode() is False

    def test_enable_sandbox_programmatically(self):
        """Test enabling sandbox via function."""
        enable_sandbox_mode()
        assert is_sandbox_mode() is True

    def test_disable_sandbox(self):
        """Test disabling sandbox."""
        enable_sandbox_mode()
        assert is_sandbox_mode() is True

        disable_sandbox_mode()
        assert is_sandbox_mode() is False

    def test_sandbox_via_environment(self):
        """Test enabling sandbox via environment variable."""
        os.environ["GMAIL_MCP_SANDBOX"] = "true"
        assert is_sandbox_mode() is True

    def test_sandbox_environment_values(self):
        """Test various environment variable values."""
        for value in ["true", "1", "yes", "TRUE", "True"]:
            os.environ["GMAIL_MCP_SANDBOX"] = value
            assert is_sandbox_mode() is True

        for value in ["false", "0", "no", ""]:
            os.environ["GMAIL_MCP_SANDBOX"] = value
            assert is_sandbox_mode() is False

    def test_custom_sandbox_config(self):
        """Test custom sandbox configuration."""
        config = SandboxConfig(
            default_user_email="test@test.com",
            message_count=100,
            latency_ms=50,
        )
        enable_sandbox_mode(config)

        loaded = get_sandbox_config()
        assert loaded.default_user_email == "test@test.com"
        assert loaded.message_count == 100
        assert loaded.latency_ms == 50


class TestMockGoogleOAuthClient:
    """Tests for mock OAuth client."""

    def setup_method(self):
        """Reset sandbox state before each test."""
        disable_sandbox_mode()

    @pytest.fixture
    def mock_client(self):
        """Create mock OAuth client."""
        return MockGoogleOAuthClient()

    def test_build_auth_url(self, mock_client):
        """Test building authorization URL."""
        url = mock_client.build_auth_url(
            state="test_state",
            code_challenge="test_challenge",
        )
        assert "sandbox" in url.lower()
        assert "test_state" in url

    @pytest.mark.asyncio
    async def test_exchange_code(self, mock_client):
        """Test token exchange."""
        response = await mock_client.exchange_code(
            code="fake_code",
            code_verifier="fake_verifier",
        )

        assert response.access_token.startswith("sandbox_access_")
        assert response.refresh_token.startswith("sandbox_refresh_")
        assert response.expires_at is not None

    @pytest.mark.asyncio
    async def test_refresh_access_token(self, mock_client):
        """Test token refresh."""
        response = await mock_client.refresh_access_token("fake_refresh_token")

        assert response.access_token.startswith("sandbox_access_")
        assert response.expires_at is not None

    @pytest.mark.asyncio
    async def test_get_user_info(self, mock_client):
        """Test getting user info."""
        user = await mock_client.get_user_info("fake_token")

        assert user.email == "sandbox@example.com"
        assert user.name == "Sandbox User"

    @pytest.mark.asyncio
    async def test_revoke_token(self, mock_client):
        """Test token revocation (no-op in sandbox)."""
        # Should not raise
        await mock_client.revoke_token("fake_token")


class TestMockGmailAPIClient:
    """Tests for mock Gmail API client."""

    def setup_method(self):
        """Reset sandbox state before each test."""
        disable_sandbox_mode()

    @pytest.fixture
    def mock_gmail(self):
        """Create mock Gmail client."""
        return MockGmailAPIClient()

    @pytest.mark.asyncio
    async def test_search_messages(self, mock_gmail):
        """Test message search."""
        result = await mock_gmail.search(token="fake", query="in:inbox")

        assert "resultSizeEstimate" in result
        assert result["resultSizeEstimate"] > 0

    @pytest.mark.asyncio
    async def test_search_unread(self, mock_gmail):
        """Test searching for unread messages."""
        result = await mock_gmail.search(token="fake", query="is:unread")

        assert "resultSizeEstimate" in result

    @pytest.mark.asyncio
    async def test_get_message(self, mock_gmail):
        """Test getting a message."""
        # First search to get a message ID
        search = await mock_gmail.search(token="fake", query="in:inbox", max_results=1)
        if search.get("messages"):
            msg_id = search["messages"][0]["id"]
            message = await mock_gmail.get_message(token="fake", message_id=msg_id)

            assert message["id"] == msg_id
            assert "payload" in message
            assert "headers" in message["payload"]

    @pytest.mark.asyncio
    async def test_get_thread(self, mock_gmail):
        """Test getting a thread."""
        # Search to get a thread ID
        search = await mock_gmail.search(token="fake", query="in:inbox", max_results=1)
        if search.get("messages"):
            thread_id = search["messages"][0]["threadId"]
            thread = await mock_gmail.get_thread(token="fake", thread_id=thread_id)

            assert thread["id"] == thread_id
            assert "messages" in thread
            assert len(thread["messages"]) > 0

    @pytest.mark.asyncio
    async def test_list_labels(self, mock_gmail):
        """Test listing labels."""
        result = await mock_gmail.list_labels(token="fake")

        assert "labels" in result
        label_ids = [l["id"] for l in result["labels"]]
        assert "INBOX" in label_ids
        assert "SENT" in label_ids

    @pytest.mark.asyncio
    async def test_get_profile(self, mock_gmail):
        """Test getting profile."""
        profile = await mock_gmail.get_profile(token="fake")

        assert profile["emailAddress"] == "sandbox@example.com"
        assert profile["messagesTotal"] > 0

    @pytest.mark.asyncio
    async def test_send_message(self, mock_gmail):
        """Test sending a message."""
        result = await mock_gmail.send_message(
            token="fake",
            raw_message="fake_base64_message",
        )

        assert "id" in result
        assert "threadId" in result
        assert result["id"].startswith("msg_")

    @pytest.mark.asyncio
    async def test_create_and_send_draft(self, mock_gmail):
        """Test draft creation and sending."""
        # Create draft
        draft = await mock_gmail.create_draft(
            token="fake",
            raw_message="fake_base64_message",
        )

        assert "id" in draft
        draft_id = draft["id"]

        # Send draft
        sent = await mock_gmail.send_draft(token="fake", draft_id=draft_id)

        assert "id" in sent
        assert sent["labelIds"] == ["SENT"]

    @pytest.mark.asyncio
    async def test_modify_labels(self, mock_gmail):
        """Test modifying message labels."""
        # Get a message
        search = await mock_gmail.search(token="fake", query="in:inbox", max_results=1)
        if search.get("messages"):
            msg_id = search["messages"][0]["id"]

            # Add starred
            result = await mock_gmail.modify_message_labels(
                token="fake",
                message_id=msg_id,
                add_labels=["STARRED"],
            )

            assert "STARRED" in result["labelIds"]

    @pytest.mark.asyncio
    async def test_trash_message(self, mock_gmail):
        """Test trashing a message."""
        search = await mock_gmail.search(token="fake", query="in:inbox", max_results=1)
        if search.get("messages"):
            msg_id = search["messages"][0]["id"]

            result = await mock_gmail.trash_message(token="fake", message_id=msg_id)

            assert "TRASH" in result["labelIds"]
            assert "INBOX" not in result["labelIds"]

    @pytest.mark.asyncio
    async def test_batch_get_messages(self, mock_gmail):
        """Test batch getting messages."""
        search = await mock_gmail.search(token="fake", query="in:inbox", max_results=5)
        if search.get("messages"):
            msg_ids = [m["id"] for m in search["messages"]]
            messages = await mock_gmail.batch_get_messages(
                token="fake",
                message_ids=msg_ids,
            )

            assert len(messages) == len(msg_ids)
