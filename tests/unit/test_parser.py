"""Tests for MIME message parser."""

from __future__ import annotations

import base64
from datetime import datetime

import pytest

from gmail_multi_user.gmail.parser import MessageParser, decode_attachment_data
from gmail_multi_user.types import Contact


class TestMessageParser:
    """Tests for MessageParser."""

    @pytest.fixture
    def parser(self):
        """Create a parser instance."""
        return MessageParser()

    def test_parse_simple_text_message(self, parser):
        """Test parsing a simple text message."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Hello World",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "body": {
                    "data": base64.urlsafe_b64encode(b"Hello World").decode(),
                },
            },
        }

        message = parser.parse(data)

        assert message.id == "msg123"
        assert message.thread_id == "thread123"
        assert message.subject == "Test Subject"
        assert message.from_.email == "sender@example.com"
        assert len(message.to) == 1
        assert message.to[0].email == "recipient@example.com"
        assert message.body_plain == "Hello World"
        assert message.body_html is None
        assert "INBOX" in message.labels
        assert not message.has_attachments

    def test_parse_html_message(self, parser):
        """Test parsing an HTML message."""
        html_content = "<html><body><h1>Hello</h1></body></html>"
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Hello",
            "labelIds": [],
            "payload": {
                "mimeType": "text/html",
                "headers": [
                    {"name": "Subject", "value": "HTML Test"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "body": {
                    "data": base64.urlsafe_b64encode(html_content.encode()).decode(),
                },
            },
        }

        message = parser.parse(data)

        assert message.body_plain == ""
        assert message.body_html == html_content

    def test_parse_multipart_alternative(self, parser):
        """Test parsing multipart/alternative message (plain + HTML)."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Plain text",
            "labelIds": [],
            "payload": {
                "mimeType": "multipart/alternative",
                "headers": [
                    {"name": "Subject", "value": "Multipart Test"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.urlsafe_b64encode(b"Plain text").decode(),
                        },
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": base64.urlsafe_b64encode(
                                b"<p>HTML text</p>"
                            ).decode(),
                        },
                    },
                ],
            },
        }

        message = parser.parse(data)

        assert message.body_plain == "Plain text"
        assert message.body_html == "<p>HTML text</p>"

    def test_parse_message_with_attachment(self, parser):
        """Test parsing message with attachment."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "See attached",
            "labelIds": [],
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "Subject", "value": "With Attachment"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.urlsafe_b64encode(
                                b"See attached file"
                            ).decode(),
                        },
                    },
                    {
                        "mimeType": "application/pdf",
                        "filename": "document.pdf",
                        "headers": [],
                        "body": {
                            "attachmentId": "att123",
                            "size": 1024,
                        },
                    },
                ],
            },
        }

        message = parser.parse(data)

        assert message.body_plain == "See attached file"
        assert message.has_attachments
        assert len(message.attachments) == 1
        assert message.attachments[0].id == "att123"
        assert message.attachments[0].filename == "document.pdf"
        assert message.attachments[0].mime_type == "application/pdf"
        assert message.attachments[0].size == 1024

    def test_parse_nested_multipart(self, parser):
        """Test parsing nested multipart message."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Nested",
            "labelIds": [],
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "Subject", "value": "Nested Multipart"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "parts": [
                    {
                        "mimeType": "multipart/alternative",
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {
                                    "data": base64.urlsafe_b64encode(
                                        b"Nested plain"
                                    ).decode(),
                                },
                            },
                            {
                                "mimeType": "text/html",
                                "body": {
                                    "data": base64.urlsafe_b64encode(
                                        b"<p>Nested HTML</p>"
                                    ).decode(),
                                },
                            },
                        ],
                    },
                    {
                        "mimeType": "image/png",
                        "filename": "image.png",
                        "headers": [],
                        "body": {
                            "attachmentId": "img123",
                            "size": 2048,
                        },
                    },
                ],
            },
        }

        message = parser.parse(data)

        assert message.body_plain == "Nested plain"
        assert message.body_html == "<p>Nested HTML</p>"
        assert len(message.attachments) == 1
        assert message.attachments[0].filename == "image.png"

    def test_parse_multiple_recipients(self, parser):
        """Test parsing message with multiple recipients."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Group email",
            "labelIds": [],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Group Test"},
                    {"name": "From", "value": '"John Doe" <john@example.com>'},
                    {
                        "name": "To",
                        "value": "alice@example.com, Bob <bob@example.com>",
                    },
                    {"name": "Cc", "value": "charlie@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
                "body": {"data": base64.urlsafe_b64encode(b"Hello all").decode()},
            },
        }

        message = parser.parse(data)

        assert message.from_.name == "John Doe"
        assert message.from_.email == "john@example.com"
        assert len(message.to) == 2
        assert message.to[0].email == "alice@example.com"
        assert message.to[1].name == "Bob"
        assert message.to[1].email == "bob@example.com"
        assert len(message.cc) == 1
        assert message.cc[0].email == "charlie@example.com"

    def test_parse_metadata_format(self, parser):
        """Test parsing metadata-only format."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Metadata only",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Metadata Test"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                ],
            },
        }

        message = parser.parse_metadata(data)

        assert message.id == "msg123"
        assert message.subject == "Metadata Test"
        assert message.body_plain == ""
        assert message.body_html is None
        assert len(message.attachments) == 0

    def test_parse_minimal_format(self, parser):
        """Test parsing minimal format."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Minimal",
            "labelIds": ["INBOX"],
        }

        message = parser.parse_minimal(data)

        assert message.id == "msg123"
        assert message.thread_id == "thread123"
        assert message.snippet == "Minimal"
        assert message.subject == ""
        assert message.from_.email == ""

    def test_parse_missing_headers(self, parser):
        """Test parsing message with missing headers."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "No headers",
            "labelIds": [],
            "payload": {
                "mimeType": "text/plain",
                "headers": [],
                "body": {"data": base64.urlsafe_b64encode(b"Body").decode()},
            },
        }

        message = parser.parse(data)

        assert message.subject == "(No Subject)"
        assert message.from_.email == ""
        assert len(message.to) == 0

    def test_parse_invalid_date(self, parser):
        """Test parsing message with invalid date."""
        data = {
            "id": "msg123",
            "threadId": "thread123",
            "snippet": "Bad date",
            "labelIds": [],
            "payload": {
                "mimeType": "text/plain",
                "headers": [
                    {"name": "Subject", "value": "Test"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Date", "value": "Not a valid date"},
                ],
                "body": {"data": ""},
            },
        }

        message = parser.parse(data)

        # Should default to current time
        assert isinstance(message.date, datetime)


class TestContact:
    """Tests for Contact.from_header()."""

    def test_parse_simple_email(self):
        """Test parsing simple email address."""
        contact = Contact.from_header("user@example.com")
        assert contact.name == ""
        assert contact.email == "user@example.com"

    def test_parse_email_with_name(self):
        """Test parsing email with name."""
        contact = Contact.from_header("John Doe <john@example.com>")
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"

    def test_parse_email_with_quoted_name(self):
        """Test parsing email with quoted name."""
        contact = Contact.from_header('"John Doe" <john@example.com>')
        assert contact.name == "John Doe"
        assert contact.email == "john@example.com"

    def test_parse_email_with_angle_brackets(self):
        """Test parsing email in angle brackets."""
        contact = Contact.from_header("<user@example.com>")
        assert contact.name == ""
        assert contact.email == "user@example.com"


class TestDecodeAttachmentData:
    """Tests for decode_attachment_data()."""

    def test_decode_valid_base64(self):
        """Test decoding valid base64url data."""
        original = b"Hello, World!"
        encoded = base64.urlsafe_b64encode(original).decode()

        result = decode_attachment_data(encoded)

        assert result == original

    def test_decode_empty_string(self):
        """Test decoding empty string."""
        result = decode_attachment_data("")
        assert result == b""

    def test_decode_invalid_base64(self):
        """Test decoding invalid base64."""
        result = decode_attachment_data("not valid base64!!!")
        assert result == b""

    def test_decode_binary_data(self):
        """Test decoding binary data."""
        original = bytes(range(256))
        encoded = base64.urlsafe_b64encode(original).decode()

        result = decode_attachment_data(encoded)

        assert result == original
