"""Tests for structured logging module."""

from __future__ import annotations

import io
import json
import logging

import pytest

from gmail_multi_user.logging import (
    HumanFormatter,
    LogContext,
    StructuredFormatter,
    StructuredLoggerAdapter,
    clear_context,
    configure_logging,
    get_context,
    get_logger,
    set_context,
)


class TestLogContext:
    """Tests for LogContext context manager."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def test_context_sets_values(self):
        """Test that LogContext sets context values."""
        with LogContext(user_id="user_123", operation="test"):
            context = get_context()
            assert context["user_id"] == "user_123"
            assert context["operation"] == "test"

    def test_context_restores_after_exit(self):
        """Test that context is restored after exiting."""
        set_context(outer="value")

        with LogContext(inner="test"):
            context = get_context()
            assert "outer" in context
            assert "inner" in context

        context = get_context()
        assert "outer" in context
        assert "inner" not in context

    def test_nested_contexts(self):
        """Test nested LogContext managers."""
        with LogContext(level1="a"):
            with LogContext(level2="b"):
                context = get_context()
                assert context["level1"] == "a"
                assert context["level2"] == "b"

            context = get_context()
            assert context["level1"] == "a"
            assert "level2" not in context


class TestStructuredFormatter:
    """Tests for JSON structured formatter."""

    def test_formats_as_json(self):
        """Test that output is valid JSON."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_includes_context(self):
        """Test that context is included in JSON."""
        clear_context()
        formatter = StructuredFormatter()

        with LogContext(user_id="user_123", request_id="req_456"):
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)

        parsed = json.loads(output)
        assert parsed["user_id"] == "user_123"
        assert parsed["request_id"] == "req_456"

    def test_includes_extra_fields(self):
        """Test that extra fields are included."""
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.custom_field = "custom_value"
        record.count = 42

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["custom_field"] == "custom_value"
        assert parsed["count"] == 42


class TestHumanFormatter:
    """Tests for human-readable formatter."""

    def test_formats_readable(self):
        """Test that output is human-readable."""
        formatter = HumanFormatter(use_colors=False)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        assert "INFO" in output
        assert "test.logger" in output
        assert "Test message" in output

    def test_includes_extra_fields(self):
        """Test that extra fields are appended."""
        clear_context()
        formatter = HumanFormatter(use_colors=False)

        with LogContext(user_id="user_123"):
            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)

        assert "user_id=user_123" in output


class TestStructuredLoggerAdapter:
    """Tests for the logger adapter."""

    def setup_method(self):
        """Set up test logger."""
        clear_context()
        self.stream = io.StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(StructuredFormatter())

        self.logger = logging.getLogger("test.adapter")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = [self.handler]
        self.logger.propagate = False

        self.adapter = StructuredLoggerAdapter(self.logger)

    def test_info_with_kwargs(self):
        """Test logging info with keyword arguments."""
        self.adapter.info("Test message", user_id="user_123", count=42)

        output = self.stream.getvalue()
        parsed = json.loads(output)

        assert parsed["message"] == "Test message"
        assert parsed["user_id"] == "user_123"
        assert parsed["count"] == 42

    def test_error_with_exception(self):
        """Test logging error with exception."""
        try:
            raise ValueError("Test error")
        except ValueError:
            self.adapter.error("Something failed", exc_info=True)

        output = self.stream.getvalue()
        parsed = json.loads(output)

        assert parsed["message"] == "Something failed"
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_adapter(self):
        """Test that get_logger returns a StructuredLoggerAdapter."""
        logger = get_logger("test.module")
        assert isinstance(logger, StructuredLoggerAdapter)

    def test_logger_name(self):
        """Test that logger has correct name."""
        logger = get_logger("my.test.logger")
        assert logger.logger.name == "my.test.logger"


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_with_json_format(self):
        """Test configuring with JSON format."""
        stream = io.StringIO()
        # Reset configured state for testing
        import gmail_multi_user.logging as log_module

        log_module._configured = False

        configure_logging(level="DEBUG", json_format=True, stream=stream)

        # Get a logger and log something
        logger = logging.getLogger("gmail_multi_user.test_config")
        logger.info("Test")

        output = stream.getvalue()
        # Should be valid JSON
        parsed = json.loads(output.strip())
        assert parsed["message"] == "Test"

        # Reset for other tests
        log_module._configured = False

    def test_configure_with_human_format(self):
        """Test configuring with human format."""
        stream = io.StringIO()
        import gmail_multi_user.logging as log_module

        log_module._configured = False

        configure_logging(level="DEBUG", json_format=False, stream=stream)

        logger = logging.getLogger("gmail_multi_user.test_human")
        logger.info("Test message")

        output = stream.getvalue()
        # Should not be JSON, should be readable
        assert "Test message" in output
        with pytest.raises(json.JSONDecodeError):
            json.loads(output.strip())

        log_module._configured = False
