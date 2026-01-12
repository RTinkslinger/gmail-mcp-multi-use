"""Gmail API client.

This module provides a low-level client for the Gmail REST API,
handling HTTP requests, authentication, and error handling.
"""

from __future__ import annotations

from typing import Any, Literal

import httpx

from gmail_multi_user.exceptions import GmailAPIError, RateLimitError

# Gmail API base URL
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"


class GmailAPIClient:
    """Low-level client for Gmail REST API.

    This client handles:
    - HTTP requests with authentication
    - Rate limit handling (429 responses)
    - Error parsing and exceptions
    - Pagination support

    Example:
        client = GmailAPIClient()
        messages = await client.search(token="...", query="is:unread")
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Gmail API client.

        Args:
            http_client: Optional httpx client for testing.
            timeout: Request timeout in seconds.
        """
        self._http_client = http_client
        self._timeout = timeout
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self._timeout)
        return self._http_client

    async def close(self) -> None:
        """Close the HTTP client if we own it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        token: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an authenticated request to Gmail API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint (e.g., "/users/me/messages").
            token: Access token for authentication.
            params: Query parameters.
            json_body: JSON request body.

        Returns:
            JSON response as dictionary.

        Raises:
            RateLimitError: If rate limited (429).
            GmailAPIError: If API returns an error.
        """
        client = await self._get_client()
        url = f"{GMAIL_API_BASE}{endpoint}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
            )
        except httpx.RequestError as e:
            raise GmailAPIError(
                message=f"Failed to connect to Gmail API: {e}",
                code="api_error",
                details={"error": str(e)},
            ) from e

        # Handle rate limiting
        if response.status_code == 429:
            retry_after_str = response.headers.get("Retry-After")
            retry_after = int(retry_after_str) if retry_after_str else None
            raise RateLimitError(
                message="Gmail API rate limit exceeded",
                retry_after=retry_after,
                details={"status_code": 429},
            )

        # Handle errors
        if response.status_code >= 400:
            self._handle_error(response)

        # Return empty dict for 204 No Content
        if response.status_code == 204:
            return {}

        return response.json()

    def _handle_error(self, response: httpx.Response) -> None:
        """Handle error responses from Gmail API.

        Args:
            response: HTTP response with error.

        Raises:
            GmailAPIError: Always raises with appropriate details.
        """
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            message = error.get("message", "Unknown error")
            code = error.get("status", "api_error")
            errors = error.get("errors", [])
        except Exception:
            message = response.text or "Unknown error"
            code = "api_error"
            errors = []

        # Map common HTTP status codes to error codes
        status_code = response.status_code
        if status_code == 401:
            code = "unauthorized"
            message = "Invalid or expired access token"
        elif status_code == 403:
            code = "permission_denied"
        elif status_code == 404:
            code = "not_found"

        raise GmailAPIError(
            message=message,
            code=code,
            details={
                "status_code": status_code,
                "errors": errors,
            },
        )

    # =========================================================================
    # Message Operations
    # =========================================================================

    async def search(
        self,
        token: str,
        query: str,
        max_results: int = 10,
        page_token: str | None = None,
        label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search for messages using Gmail query syntax.

        Args:
            token: Access token.
            query: Gmail search query (e.g., "is:unread from:boss").
            max_results: Maximum number of results (1-500).
            page_token: Token for pagination.
            label_ids: Filter by label IDs.

        Returns:
            Dict with 'messages' (list of {id, threadId}),
            'nextPageToken', and 'resultSizeEstimate'.
        """
        params: dict[str, Any] = {
            "q": query,
            "maxResults": min(max_results, 500),
        }

        if page_token:
            params["pageToken"] = page_token

        if label_ids:
            params["labelIds"] = label_ids

        return await self._make_request(
            method="GET",
            endpoint="/users/me/messages",
            token=token,
            params=params,
        )

    async def get_message(
        self,
        token: str,
        message_id: str,
        format: Literal["full", "metadata", "minimal", "raw"] = "full",
        metadata_headers: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get a single message by ID.

        Args:
            token: Access token.
            message_id: Message ID.
            format: Response format:
                - "full": Returns full email content
                - "metadata": Returns headers only
                - "minimal": Returns id, threadId, labelIds, snippet
                - "raw": Returns entire email as base64url string
            metadata_headers: Headers to include when format="metadata".

        Returns:
            Full message data from Gmail API.
        """
        params: dict[str, Any] = {"format": format}

        if format == "metadata" and metadata_headers:
            params["metadataHeaders"] = metadata_headers

        return await self._make_request(
            method="GET",
            endpoint=f"/users/me/messages/{message_id}",
            token=token,
            params=params,
        )

    async def batch_get_messages(
        self,
        token: str,
        message_ids: list[str],
        format: Literal["full", "metadata", "minimal"] = "metadata",
    ) -> list[dict[str, Any]]:
        """Get multiple messages efficiently.

        Note: This uses individual requests for now.
        A true batch implementation would use Gmail's batch endpoint.

        Args:
            token: Access token.
            message_ids: List of message IDs.
            format: Response format.

        Returns:
            List of message data dictionaries.
        """
        # For simplicity, we fetch messages individually
        # A production implementation would use the batch endpoint
        messages = []
        for msg_id in message_ids:
            try:
                msg = await self.get_message(token, msg_id, format)
                messages.append(msg)
            except GmailAPIError as e:
                if e.details and e.details.get("status_code") == 404:
                    continue  # Skip not found messages
                raise
        return messages

    # =========================================================================
    # Thread Operations
    # =========================================================================

    async def get_thread(
        self,
        token: str,
        thread_id: str,
        format: Literal["full", "metadata", "minimal"] = "full",
    ) -> dict[str, Any]:
        """Get all messages in a thread.

        Args:
            token: Access token.
            thread_id: Thread ID.
            format: Response format for messages.

        Returns:
            Thread data with 'id', 'historyId', and 'messages'.
        """
        params = {"format": format}

        return await self._make_request(
            method="GET",
            endpoint=f"/users/me/threads/{thread_id}",
            token=token,
            params=params,
        )

    # =========================================================================
    # Label Operations
    # =========================================================================

    async def list_labels(self, token: str) -> dict[str, Any]:
        """List all labels for the account.

        Args:
            token: Access token.

        Returns:
            Dict with 'labels' list containing label data.
        """
        return await self._make_request(
            method="GET",
            endpoint="/users/me/labels",
            token=token,
        )

    async def get_label(self, token: str, label_id: str) -> dict[str, Any]:
        """Get a specific label with message counts.

        Args:
            token: Access token.
            label_id: Label ID.

        Returns:
            Label data including messagesTotal and messagesUnread.
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/users/me/labels/{label_id}",
            token=token,
        )

    # =========================================================================
    # Attachment Operations
    # =========================================================================

    async def get_attachment(
        self,
        token: str,
        message_id: str,
        attachment_id: str,
    ) -> dict[str, Any]:
        """Get attachment data.

        Args:
            token: Access token.
            message_id: Message ID containing the attachment.
            attachment_id: Attachment ID.

        Returns:
            Dict with 'size' and 'data' (base64url encoded).
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/users/me/messages/{message_id}/attachments/{attachment_id}",
            token=token,
        )

    # =========================================================================
    # Profile Operations
    # =========================================================================

    async def get_profile(self, token: str) -> dict[str, Any]:
        """Get Gmail profile information.

        Args:
            token: Access token.

        Returns:
            Dict with 'emailAddress', 'messagesTotal',
            'threadsTotal', 'historyId'.
        """
        return await self._make_request(
            method="GET",
            endpoint="/users/me/profile",
            token=token,
        )

    # =========================================================================
    # Send Operations
    # =========================================================================

    async def send_message(
        self,
        token: str,
        raw_message: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Send an email message.

        Args:
            token: Access token.
            raw_message: Base64url encoded MIME message.
            thread_id: Optional thread ID for replies.

        Returns:
            Dict with 'id', 'threadId', and 'labelIds'.
        """
        body: dict[str, Any] = {"raw": raw_message}
        if thread_id:
            body["threadId"] = thread_id

        return await self._make_request(
            method="POST",
            endpoint="/users/me/messages/send",
            token=token,
            json_body=body,
        )

    # =========================================================================
    # Draft Operations
    # =========================================================================

    async def create_draft(
        self,
        token: str,
        raw_message: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a draft email.

        Args:
            token: Access token.
            raw_message: Base64url encoded MIME message.
            thread_id: Optional thread ID for reply drafts.

        Returns:
            Dict with 'id' (draft ID) and 'message' containing message data.
        """
        message: dict[str, Any] = {"raw": raw_message}
        if thread_id:
            message["threadId"] = thread_id

        return await self._make_request(
            method="POST",
            endpoint="/users/me/drafts",
            token=token,
            json_body={"message": message},
        )

    async def get_draft(
        self,
        token: str,
        draft_id: str,
        format: Literal["full", "metadata", "minimal"] = "full",
    ) -> dict[str, Any]:
        """Get a draft by ID.

        Args:
            token: Access token.
            draft_id: Draft ID.
            format: Response format for the message.

        Returns:
            Dict with 'id' and 'message' containing the draft message.
        """
        return await self._make_request(
            method="GET",
            endpoint=f"/users/me/drafts/{draft_id}",
            token=token,
            params={"format": format},
        )

    async def update_draft(
        self,
        token: str,
        draft_id: str,
        raw_message: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing draft.

        Args:
            token: Access token.
            draft_id: Draft ID to update.
            raw_message: New base64url encoded MIME message.
            thread_id: Optional thread ID.

        Returns:
            Updated draft data.
        """
        message: dict[str, Any] = {"raw": raw_message}
        if thread_id:
            message["threadId"] = thread_id

        return await self._make_request(
            method="PUT",
            endpoint=f"/users/me/drafts/{draft_id}",
            token=token,
            json_body={"message": message},
        )

    async def send_draft(self, token: str, draft_id: str) -> dict[str, Any]:
        """Send an existing draft.

        Args:
            token: Access token.
            draft_id: Draft ID to send.

        Returns:
            Sent message data with 'id' and 'threadId'.
        """
        return await self._make_request(
            method="POST",
            endpoint="/users/me/drafts/send",
            token=token,
            json_body={"id": draft_id},
        )

    async def delete_draft(self, token: str, draft_id: str) -> dict[str, Any]:
        """Delete a draft.

        Args:
            token: Access token.
            draft_id: Draft ID to delete.

        Returns:
            Empty dict on success.
        """
        return await self._make_request(
            method="DELETE",
            endpoint=f"/users/me/drafts/{draft_id}",
            token=token,
        )

    async def list_drafts(
        self,
        token: str,
        max_results: int = 10,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List drafts.

        Args:
            token: Access token.
            max_results: Maximum number of results.
            page_token: Token for pagination.

        Returns:
            Dict with 'drafts' list and optional 'nextPageToken'.
        """
        params: dict[str, Any] = {"maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token

        return await self._make_request(
            method="GET",
            endpoint="/users/me/drafts",
            token=token,
            params=params,
        )

    # =========================================================================
    # Label Modification Operations
    # =========================================================================

    async def modify_message_labels(
        self,
        token: str,
        message_id: str,
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Modify labels on a message.

        Args:
            token: Access token.
            message_id: Message ID to modify.
            add_labels: Label IDs to add.
            remove_labels: Label IDs to remove.

        Returns:
            Updated message data with 'id', 'threadId', 'labelIds'.
        """
        body: dict[str, Any] = {}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        return await self._make_request(
            method="POST",
            endpoint=f"/users/me/messages/{message_id}/modify",
            token=token,
            json_body=body,
        )

    async def batch_modify_labels(
        self,
        token: str,
        message_ids: list[str],
        add_labels: list[str] | None = None,
        remove_labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Modify labels on multiple messages.

        Args:
            token: Access token.
            message_ids: List of message IDs to modify.
            add_labels: Label IDs to add.
            remove_labels: Label IDs to remove.

        Returns:
            Empty dict on success.
        """
        body: dict[str, Any] = {"ids": message_ids}
        if add_labels:
            body["addLabelIds"] = add_labels
        if remove_labels:
            body["removeLabelIds"] = remove_labels

        return await self._make_request(
            method="POST",
            endpoint="/users/me/messages/batchModify",
            token=token,
            json_body=body,
        )

    # =========================================================================
    # Trash Operations
    # =========================================================================

    async def trash_message(self, token: str, message_id: str) -> dict[str, Any]:
        """Move a message to trash.

        Args:
            token: Access token.
            message_id: Message ID to trash.

        Returns:
            Updated message data.
        """
        return await self._make_request(
            method="POST",
            endpoint=f"/users/me/messages/{message_id}/trash",
            token=token,
        )

    async def untrash_message(self, token: str, message_id: str) -> dict[str, Any]:
        """Remove a message from trash.

        Args:
            token: Access token.
            message_id: Message ID to untrash.

        Returns:
            Updated message data.
        """
        return await self._make_request(
            method="POST",
            endpoint=f"/users/me/messages/{message_id}/untrash",
            token=token,
        )
