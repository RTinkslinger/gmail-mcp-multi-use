"""Email message composer for Gmail API.

This module builds MIME messages for sending via the Gmail API,
handling plain text, HTML, attachments, and reply threading.
"""

from __future__ import annotations

import base64
import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gmail_multi_user.types import AttachmentInput, Message


class MessageComposer:
    """Composes MIME messages for the Gmail API.

    Handles:
    - Plain text messages
    - HTML messages with multipart/alternative
    - Attachments with multipart/mixed
    - Reply threading with proper headers

    Example:
        composer = MessageComposer()
        raw = composer.compose(
            to=["bob@example.com"],
            subject="Hello",
            body="Hi Bob!",
        )
        # raw is base64url encoded, ready for Gmail API
    """

    def compose(
        self,
        to: list[str],
        subject: str,
        body: str,
        body_html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        from_address: str | None = None,
        reply_to: str | None = None,
        attachments: list[AttachmentInput] | None = None,
        in_reply_to: str | None = None,
        references: str | None = None,
        thread_id: str | None = None,
    ) -> str:
        """Compose a MIME message for sending.

        Args:
            to: Recipient email addresses.
            subject: Email subject.
            body: Plain text body.
            body_html: Optional HTML body.
            cc: CC recipients.
            bcc: BCC recipients.
            from_address: From address (usually set by Gmail).
            reply_to: Reply-To address.
            attachments: List of attachments.
            in_reply_to: Message-ID for reply threading.
            references: References header for threading.
            thread_id: Gmail thread ID for threading.

        Returns:
            Base64url encoded raw message for Gmail API.
        """
        # Determine message structure
        has_html = body_html is not None
        has_attachments = attachments and len(attachments) > 0

        if has_attachments:
            # multipart/mixed with text (or alternative) + attachments
            msg = MIMEMultipart("mixed")
            if has_html:
                # Text part is multipart/alternative
                text_part = self._create_alternative_part(body, body_html)
            else:
                text_part = self._create_text_part(body)
            msg.attach(text_part)

            # Add attachments
            for attachment in attachments:
                att_part = self._create_attachment_part(attachment)
                msg.attach(att_part)

        elif has_html:
            # multipart/alternative with plain + HTML
            msg = self._create_alternative_part(body, body_html)

        else:
            # Simple plain text
            msg = self._create_text_part(body)

        # Set headers
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        if from_address:
            msg["From"] = from_address
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)
        if reply_to:
            msg["Reply-To"] = reply_to

        # Threading headers
        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
        if references:
            msg["References"] = references

        return self._encode_message(msg)

    def compose_reply(
        self,
        original_message: Message,
        body: str,
        body_html: str | None = None,
        reply_all: bool = False,
        attachments: list[AttachmentInput] | None = None,
    ) -> tuple[str, str | None]:
        """Compose a reply to an existing message.

        Args:
            original_message: The message being replied to.
            body: Reply body text.
            body_html: Optional HTML body.
            reply_all: Include all original recipients.
            attachments: Optional attachments.

        Returns:
            Tuple of (base64url encoded message, thread_id).
        """
        # Determine recipients
        to = [original_message.from_.email]
        cc = None

        if reply_all:
            # Add original To recipients (excluding self)
            # Add original CC recipients
            [c.email for c in original_message.to]
            cc = [c.email for c in original_message.cc]

        # Build subject
        subject = original_message.subject
        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"

        # Get threading headers
        # The In-Reply-To should be the Message-ID of the original
        # For simplicity, we use the Gmail message ID
        in_reply_to = f"<{original_message.id}@mail.gmail.com>"

        # References should include all previous message IDs
        references = in_reply_to

        raw = self.compose(
            to=to,
            subject=subject,
            body=body,
            body_html=body_html,
            cc=cc,
            attachments=attachments,
            in_reply_to=in_reply_to,
            references=references,
        )

        return raw, original_message.thread_id

    def _create_text_part(self, body: str) -> MIMEText:
        """Create a plain text MIME part.

        Args:
            body: Plain text content.

        Returns:
            MIMEText part.
        """
        return MIMEText(body, "plain", "utf-8")

    def _create_html_part(self, body_html: str) -> MIMEText:
        """Create an HTML MIME part.

        Args:
            body_html: HTML content.

        Returns:
            MIMEText part with HTML subtype.
        """
        return MIMEText(body_html, "html", "utf-8")

    def _create_alternative_part(
        self, body: str, body_html: str
    ) -> MIMEMultipart:
        """Create a multipart/alternative with plain and HTML.

        Args:
            body: Plain text content.
            body_html: HTML content.

        Returns:
            MIMEMultipart with both parts.
        """
        msg = MIMEMultipart("alternative")
        msg.attach(self._create_text_part(body))
        msg.attach(self._create_html_part(body_html))
        return msg

    def _create_attachment_part(
        self, attachment: AttachmentInput
    ) -> MIMEBase:
        """Create an attachment MIME part.

        Args:
            attachment: Attachment data.

        Returns:
            MIMEBase part with attachment.
        """
        # Parse mime type
        maintype, subtype = attachment.mime_type.split("/", 1)

        part = MIMEBase(maintype, subtype)
        part.set_payload(attachment.content)

        # Encode as base64
        encoders.encode_base64(part)

        # Set Content-Disposition header
        part.add_header(
            "Content-Disposition",
            "attachment",
            filename=attachment.filename,
        )

        return part

    def _encode_message(self, msg: MIMEBase) -> str:
        """Encode a MIME message for the Gmail API.

        Args:
            msg: MIME message to encode.

        Returns:
            Base64url encoded string.
        """
        raw_bytes = msg.as_bytes()
        return base64.urlsafe_b64encode(raw_bytes).decode("utf-8")


def guess_mime_type(filename: str) -> str:
    """Guess the MIME type for a filename.

    Args:
        filename: Name of the file.

    Returns:
        MIME type string (defaults to application/octet-stream).
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"
