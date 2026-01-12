"""Unit tests for MessageComposer."""

from __future__ import annotations

import base64
from email import message_from_bytes

from gmail_multi_user.gmail.composer import MessageComposer, guess_mime_type
from gmail_multi_user.types import AttachmentInput, Contact, Message


class TestMessageComposer:
    """Tests for MessageComposer class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.composer = MessageComposer()

    def test_compose_simple_text_email(self) -> None:
        """Test composing a simple plain text email."""
        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="Hello",
            body="Hi Bob!",
        )

        # Decode and parse
        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg["To"] == "bob@example.com"
        assert msg["Subject"] == "Hello"
        assert msg.get_content_type() == "text/plain"
        assert "Hi Bob!" in msg.get_payload(decode=True).decode()

    def test_compose_multiple_recipients(self) -> None:
        """Test composing email with multiple To recipients."""
        raw = self.composer.compose(
            to=["alice@example.com", "bob@example.com"],
            subject="Group message",
            body="Hello everyone!",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert "alice@example.com" in msg["To"]
        assert "bob@example.com" in msg["To"]

    def test_compose_with_cc_and_bcc(self) -> None:
        """Test composing email with CC and BCC."""
        raw = self.composer.compose(
            to=["alice@example.com"],
            subject="Test",
            body="Content",
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg["Cc"] == "cc@example.com"
        assert msg["Bcc"] == "bcc@example.com"

    def test_compose_with_from_and_reply_to(self) -> None:
        """Test composing email with From and Reply-To headers."""
        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="Test",
            body="Content",
            from_address="sender@example.com",
            reply_to="replies@example.com",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg["From"] == "sender@example.com"
        assert msg["Reply-To"] == "replies@example.com"

    def test_compose_html_email(self) -> None:
        """Test composing email with HTML body."""
        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="HTML Test",
            body="Plain text version",
            body_html="<h1>HTML version</h1>",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        # Should be multipart/alternative
        assert msg.get_content_type() == "multipart/alternative"

        parts = msg.get_payload()
        assert len(parts) == 2

        # First part is plain text
        assert parts[0].get_content_type() == "text/plain"
        assert "Plain text" in parts[0].get_payload(decode=True).decode()

        # Second part is HTML
        assert parts[1].get_content_type() == "text/html"
        assert "<h1>HTML version</h1>" in parts[1].get_payload(decode=True).decode()

    def test_compose_with_attachment(self) -> None:
        """Test composing email with attachment."""
        attachment = AttachmentInput(
            filename="test.txt",
            mime_type="text/plain",
            content=b"Hello attachment!",
        )

        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="With Attachment",
            body="See attached",
            attachments=[attachment],
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        # Should be multipart/mixed
        assert msg.get_content_type() == "multipart/mixed"

        parts = msg.get_payload()
        assert len(parts) == 2

        # First part is text
        assert parts[0].get_content_type() == "text/plain"

        # Second part is attachment
        assert parts[1].get_filename() == "test.txt"
        assert parts[1].get_content_type() == "text/plain"

    def test_compose_html_with_attachment(self) -> None:
        """Test composing HTML email with attachment."""
        attachment = AttachmentInput(
            filename="image.png",
            mime_type="image/png",
            content=b"\x89PNG\r\n\x1a\n",  # PNG header
        )

        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="HTML with Attachment",
            body="Plain text",
            body_html="<h1>HTML</h1>",
            attachments=[attachment],
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        # Should be multipart/mixed
        assert msg.get_content_type() == "multipart/mixed"

        parts = msg.get_payload()
        assert len(parts) == 2

        # First part is multipart/alternative (text + html)
        assert parts[0].get_content_type() == "multipart/alternative"

        # Second part is attachment
        assert parts[1].get_filename() == "image.png"

    def test_compose_multiple_attachments(self) -> None:
        """Test composing email with multiple attachments."""
        attachments = [
            AttachmentInput(
                filename="doc1.pdf",
                mime_type="application/pdf",
                content=b"%PDF-1.4",
            ),
            AttachmentInput(
                filename="doc2.pdf",
                mime_type="application/pdf",
                content=b"%PDF-1.5",
            ),
        ]

        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="Multiple Attachments",
            body="Two files attached",
            attachments=attachments,
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        parts = msg.get_payload()
        assert len(parts) == 3  # text + 2 attachments

        filenames = [p.get_filename() for p in parts if p.get_filename()]
        assert "doc1.pdf" in filenames
        assert "doc2.pdf" in filenames

    def test_compose_with_threading_headers(self) -> None:
        """Test composing email with threading headers."""
        raw = self.composer.compose(
            to=["bob@example.com"],
            subject="Re: Original",
            body="Reply content",
            in_reply_to="<original@mail.gmail.com>",
            references="<original@mail.gmail.com>",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg["In-Reply-To"] == "<original@mail.gmail.com>"
        assert msg["References"] == "<original@mail.gmail.com>"

    def test_compose_reply(self) -> None:
        """Test composing a reply to an existing message."""
        original = Message(
            id="msg123",
            thread_id="thread456",
            subject="Hello",
            from_=Contact(name="Alice", email="alice@example.com"),
            to=[Contact(name="Bob", email="bob@example.com")],
            cc=[],
            bcc=[],
            date=None,
            snippet="Original message",
            body_plain="Original body",
            body_html=None,
            labels=["INBOX"],
            attachments=[],
            has_attachments=False,
        )

        raw, thread_id = self.composer.compose_reply(
            original_message=original,
            body="Thanks for the message!",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg["To"] == "alice@example.com"
        assert msg["Subject"] == "Re: Hello"
        assert msg["In-Reply-To"] == "<msg123@mail.gmail.com>"
        assert thread_id == "thread456"

    def test_compose_reply_preserves_re_prefix(self) -> None:
        """Test that Re: prefix is not duplicated."""
        original = Message(
            id="msg123",
            thread_id="thread456",
            subject="Re: Already a reply",
            from_=Contact(name="Alice", email="alice@example.com"),
            to=[Contact(name="Bob", email="bob@example.com")],
            cc=[],
            bcc=[],
            date=None,
            snippet="",
            body_plain="",
            body_html=None,
            labels=["INBOX"],
            attachments=[],
            has_attachments=False,
        )

        raw, _ = self.composer.compose_reply(
            original_message=original,
            body="Reply",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg["Subject"] == "Re: Already a reply"
        assert not msg["Subject"].startswith("Re: Re:")

    def test_compose_reply_with_html(self) -> None:
        """Test composing HTML reply."""
        original = Message(
            id="msg123",
            thread_id="thread456",
            subject="Test",
            from_=Contact(name="Alice", email="alice@example.com"),
            to=[],
            cc=[],
            bcc=[],
            date=None,
            snippet="",
            body_plain="",
            body_html=None,
            labels=["INBOX"],
            attachments=[],
            has_attachments=False,
        )

        raw, _ = self.composer.compose_reply(
            original_message=original,
            body="Plain reply",
            body_html="<p>HTML reply</p>",
        )

        msg_bytes = base64.urlsafe_b64decode(raw)
        msg = message_from_bytes(msg_bytes)

        assert msg.get_content_type() == "multipart/alternative"


class TestGuessMimeType:
    """Tests for guess_mime_type function."""

    def test_guess_text_plain(self) -> None:
        """Test guessing text/plain for .txt files."""
        assert guess_mime_type("document.txt") == "text/plain"

    def test_guess_image_png(self) -> None:
        """Test guessing image/png for .png files."""
        assert guess_mime_type("photo.png") == "image/png"

    def test_guess_image_jpeg(self) -> None:
        """Test guessing image/jpeg for .jpg files."""
        assert guess_mime_type("photo.jpg") == "image/jpeg"

    def test_guess_application_pdf(self) -> None:
        """Test guessing application/pdf for .pdf files."""
        assert guess_mime_type("document.pdf") == "application/pdf"

    def test_guess_unknown_returns_octet_stream(self) -> None:
        """Test that unknown extensions return application/octet-stream."""
        assert guess_mime_type("file.unknownextension123") == "application/octet-stream"

    def test_guess_no_extension(self) -> None:
        """Test that files without extension return octet-stream."""
        assert guess_mime_type("noextension") == "application/octet-stream"
