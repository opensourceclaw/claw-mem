# Copyright 2026 Peter Cheng
"""Structured JSON logging configuration (v2.20.0)."""

import logging
import json
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional


@dataclass
class LogConfig:
    """Logging configuration."""

    level: str = "INFO"                  # DEBUG / INFO / WARNING / ERROR
    output: str = "stderr"               # stderr / file path
    json_format: bool = True             # JSON format (vs plain text)
    logger_name: str = "claw_mem"        # Root logger name
    include_extra: bool = True           # Include extra fields in JSON


class JsonFormatter(logging.Formatter):
    """JSON structured log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Include extra dict fields from the record
        if hasattr(record, 'extra_fields') and record.extra_fields:
            base.update(record.extra_fields)
        return json.dumps(base, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    """Plain text formatter with timestamp."""

    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S',
        )


def setup_logging(config: Optional[LogConfig] = None) -> logging.Logger:
    """Configure structured logging.

    Args:
        config: LogConfig or None (uses defaults).

    Returns:
        Configured root logger for 'claw_mem'.
    """
    cfg = config or LogConfig()

    logger = logging.getLogger(cfg.logger_name)
    logger.setLevel(getattr(logging, cfg.level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = JsonFormatter() if cfg.json_format else PlainFormatter()

    if cfg.output == "stderr":
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = logging.FileHandler(cfg.output, encoding='utf-8')

    handler.setFormatter(fmt)
    logger.addHandler(handler)

    return logger
