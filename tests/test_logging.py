"""Tests for structured logging (v2.20.0)."""

import json
import logging
import pytest
from claw_mem.logging_config import (
    LogConfig,
    JsonFormatter,
    PlainFormatter,
    setup_logging,
)


class TestLogConfig:
    """Tests for LogConfig dataclass."""

    def test_defaults(self):
        cfg = LogConfig()
        assert cfg.level == "INFO"
        assert cfg.output == "stderr"
        assert cfg.json_format is True
        assert cfg.logger_name == "claw_mem"

    def test_custom(self):
        cfg = LogConfig(level="DEBUG", output="/tmp/test.log", json_format=False)
        assert cfg.level == "DEBUG"
        assert cfg.output == "/tmp/test.log"
        assert cfg.json_format is False


class TestJsonFormatter:
    """Tests for JSON log formatting."""

    def test_format_basic(self):
        fmt = JsonFormatter()
        record = logging.LogRecord("test", logging.INFO, "", 0, "hello world", (), None)
        output = fmt.format(record)
        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "hello world"
        assert "timestamp" in data

    def test_format_with_extra(self):
        fmt = JsonFormatter()
        record = logging.LogRecord(
            "claw_mem.manager", logging.WARNING, "", 0, "store_completed", (), None
        )
        record.extra_fields = {"memory_id": "mem_abc", "store_time_ms": 1.23}
        output = fmt.format(record)
        data = json.loads(output)
        assert data["memory_id"] == "mem_abc"
        assert data["store_time_ms"] == 1.23

    def test_format_json_valid(self):
        fmt = JsonFormatter()
        record = logging.LogRecord(
            "app", logging.ERROR, "", 0, 'message with "quotes" and \n newline', (), None
        )
        output = fmt.format(record)
        data = json.loads(output)
        assert data["level"] == "ERROR"


class TestSetupLogging:
    """Tests for setup_logging."""

    def test_default_setup(self):
        logger = setup_logging()
        assert logger.name == "claw_mem"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1

    def test_debug_level(self):
        logger = setup_logging(LogConfig(level="DEBUG"))
        assert logger.level == logging.DEBUG
