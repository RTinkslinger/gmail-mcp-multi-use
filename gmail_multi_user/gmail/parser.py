"""MIME message parser for Gmail API responses.

This module parses Gmail API message payloads into structured
Message objects, handling multipart MIME content, attachments,
and various encodings.
"""

from __future__ import annotations

import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

from gmail_multi_user.types import Attachment, Contact, Message


class MessageParser:
    """Parser for Gmail API message payloads.

    Handles:
    - Header extraction (From, To, CC, BCC, Subject, Date)
    - Multipart MIME content parsing
    - Body extraction (plain text and HTML)
    - Attachment listing
    - Base64 decoding

    Example:
        parser = MessageParser()
        message = parser.parse(gmail_api_response)
    """

    # Standard headers to extract
    STANDARD_HEADERS = [
        "From",
        "To",
        "Cc",
        "Bcc",
        "Subject",
        "Date",
        "Message-ID",
        "In-Reply-To",
        "References",
    ]

    def parse(self, data: dict[str, Any]) -> Message:
        """Parse a Gmail API message response into a Message object.

        Args:
            data: Raw message data from Gmail API (format="full").

        Returns:
            Parsed Message object.
        """
        message_id = data.get("id", "")
        thread_id = data.get("threadId", "")
        snippet = data.get("snippet", "")
        labels = data.get("labelIds", [])

        payload = data.get("payload", {})
        headers = self._parse_headers(payload.get("headers", []))

        # Parse contacts
        from_contact = Contact.from_header(headers.get("From", ""))
        to_contacts = self._parse_address_list(headers.get("To", ""))
        cc_contacts = self._parse_address_list(headers.get("Cc", ""))
        bcc_contacts = self._parse_address_list(headers.get("Bcc", ""))

        # Parse date
        date = self._parse_date(headers.get("Date", ""))

        # Parse body and attachments
        body_plain, body_html, attachments = self._parse_payload(payload)

        return Message(
            id=message_id,
            thread_id=thread_id,
            subject=headers.get("Subject", "(No Subject)"),
            from_=from_contact,
            to=to_contacts,
            cc=cc_contacts,
            bcc=bcc_contacts,
            date=date,
            snippet=snippet,
            body_plain=body_plain,
            body_html=body_html,
            labels=labels,
            attachments=attachments,
            has_attachments=len(attachments) > 0,
        )

    def parse_metadata(self, data: dict[str, Any]) -> Message:
        """Parse a Gmail API message with metadata format.

        Args:
            data: Raw message data from Gmail API (format="metadata").

        Returns:
            Message with headers but no body content.
        """
        message_id = data.get("id", "")
        thread_id = data.get("threadId", "")
        snippet = data.get("snippet", "")
        labels = data.get("labelIds", [])

        payload = data.get("payload", {})
        headers = self._parse_headers(payload.get("headers", []))

        from_contact = Contact.from_header(headers.get("From", ""))
        to_contacts = self._parse_address_list(headers.get("To", ""))
        cc_contacts = self._parse_address_list(headers.get("Cc", ""))
        bcc_contacts = self._parse_address_list(headers.get("Bcc", ""))
        date = self._parse_date(headers.get("Date", ""))

        return Message(
            id=message_id,
            thread_id=thread_id,
            subject=headers.get("Subject", "(No Subject)"),
            from_=from_contact,
            to=to_contacts,
            cc=cc_contacts,
            bcc=bcc_contacts,
            date=date,
            snippet=snippet,
            body_plain="",
            body_html=None,
            labels=labels,
            attachments=[],
            has_attachments=False,
        )

    def parse_minimal(self, data: dict[str, Any]) -> Message:
        """Parse a Gmail API message with minimal format.

        Args:
            data: Raw message data from Gmail API (format="minimal").

        Returns:
            Message with only id, threadId, labelIds, snippet.
        """
        return Message(
            id=data.get("id", ""),
            thread_id=data.get("threadId", ""),
            subject="",
            from_=Contact(name="", email=""),
            to=[],
            cc=[],
            bcc=[],
            date=datetime.utcnow(),
            snippet=data.get("snippet", ""),
            body_plain="",
            body_html=None,
            labels=data.get("labelIds", []),
            attachments=[],
            has_attachments=False,
        )

    def _parse_headers(self, headers: list[dict[str, str]]) -> dict[str, str]:
        """Convert Gmail headers list to dictionary.

        Args:
            headers: List of {"name": ..., "value": ...} dicts.

        Returns:
            Dictionary of header name -> value.
        """
        return {h["name"]: h["value"] for h in headers if "name" in h and "value" in h}

    def _parse_address_list(self, header: str) -> list[Contact]:
        """Parse a comma-separated list of email addresses.

        Args:
            header: Address list like "Alice <a@x.com>, Bob <b@x.com>".

        Returns:
            List of Contact objects.
        """
        if not header:
            return []

        # Split by comma, but not commas inside quotes
        addresses = []
        current = ""
        in_quotes = False

        for char in header:
            if char == '"':
                in_quotes = not in_quotes
            elif char == "," and not in_quotes:
                if current.strip():
                    addresses.append(Contact.from_header(current.strip()))
                current = ""
                continue
            current += char

        if current.strip():
            addresses.append(Contact.from_header(current.strip()))

        return addresses

    def _parse_date(self, date_str: str) -> datetime:
        """Parse email date header into datetime.

        Args:
            date_str: RFC 2822 date string.

        Returns:
            Parsed datetime (UTC if no timezone).
        """
        if not date_str:
            return datetime.utcnow()

        try:
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()

    def _parse_payload(
        self, payload: dict[str, Any]
    ) -> tuple[str, str | None, list[Attachment]]:
        """Parse message payload for body content and attachments.

        Args:
            payload: Message payload from Gmail API.

        Returns:
            Tuple of (body_plain, body_html, attachments).
        """
        body_plain = ""
        body_html: str | None = None
        attachments: list[Attachment] = []

        mime_type = payload.get("mimeType", "")

        if mime_type.startswith("multipart/"):
            # Recursively process parts
            parts = payload.get("parts", [])
            body_plain, body_html, attachments = self._parse_parts(parts)
        else:
            # Single part message
            body = payload.get("body", {})
            data = body.get("data", "")

            if data:
                decoded = self._decode_body(data)
                if mime_type == "text/plain":
                    body_plain = decoded
                elif mime_type == "text/html":
                    body_html = decoded

            # Check for attachment
            if body.get("attachmentId"):
                attachment = self._extract_attachment(payload, body)
                if attachment:
                    attachments.append(attachment)

        return body_plain, body_html, attachments

    def _parse_parts(
        self, parts: list[dict[str, Any]]
    ) -> tuple[str, str | None, list[Attachment]]:
        """Recursively parse MIME parts.

        Args:
            parts: List of MIME parts.

        Returns:
            Tuple of (body_plain, body_html, attachments).
        """
        body_plain = ""
        body_html: str | None = None
        attachments: list[Attachment] = []

        for part in parts:
            mime_type = part.get("mimeType", "")
            body = part.get("body", {})

            if mime_type.startswith("multipart/"):
                # Nested multipart - recurse
                nested_parts = part.get("parts", [])
                nested_plain, nested_html, nested_attachments = self._parse_parts(
                    nested_parts
                )
                if nested_plain and not body_plain:
                    body_plain = nested_plain
                if nested_html and not body_html:
                    body_html = nested_html
                attachments.extend(nested_attachments)

            elif mime_type == "text/plain":
                data = body.get("data", "")
                if data and not body_plain:
                    body_plain = self._decode_body(data)

            elif mime_type == "text/html":
                data = body.get("data", "")
                if data and not body_html:
                    body_html = self._decode_body(data)

            else:
                # Check for attachment
                attachment = self._extract_attachment(part, body)
                if attachment:
                    attachments.append(attachment)

        return body_plain, body_html, attachments

    def _extract_attachment(
        self, part: dict[str, Any], body: dict[str, Any]
    ) -> Attachment | None:
        """Extract attachment metadata from a MIME part.

        Args:
            part: MIME part data.
            body: Body data from the part.

        Returns:
            Attachment object or None if not an attachment.
        """
        attachment_id = body.get("attachmentId")
        if not attachment_id:
            return None

        headers = self._parse_headers(part.get("headers", []))
        filename = part.get("filename", "")

        # Try to get filename from Content-Disposition header
        if not filename:
            content_disp = headers.get("Content-Disposition", "")
            if "filename=" in content_disp:
                # Extract filename from Content-Disposition
                import re

                match = re.search(r'filename="?([^";\n]+)"?', content_disp)
                if match:
                    filename = match.group(1)

        if not filename:
            filename = "attachment"

        return Attachment(
            id=attachment_id,
            filename=filename,
            mime_type=part.get("mimeType", "application/octet-stream"),
            size=body.get("size", 0),
        )

    def _decode_body(self, data: str) -> str:
        """Decode base64url encoded body data.

        Args:
            data: Base64url encoded string.

        Returns:
            Decoded string (UTF-8).
        """
        if not data:
            return ""

        try:
            # Gmail uses URL-safe base64 encoding
            decoded_bytes = base64.urlsafe_b64decode(data)
            return decoded_bytes.decode("utf-8", errors="replace")
        except Exception:
            return ""


def decode_attachment_data(data: str) -> bytes:
    """Decode base64url encoded attachment data.

    Args:
        data: Base64url encoded string from Gmail API.

    Returns:
        Decoded bytes.
    """
    if not data:
        return b""

    try:
        return base64.urlsafe_b64decode(data)
    except Exception:
        return b""
