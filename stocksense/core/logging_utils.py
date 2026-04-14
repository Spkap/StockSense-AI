"""
Structured logging helper for StockSense.

Usage:
    from stocksense.core.logging_utils import get_logger
    logger = get_logger(__name__)
    logger.info("Analysis complete", ticker="AAPL", duration_ms=1240, correlation_id="a3f9b12c")
"""
import logging
import json
from typing import Any


class StructuredLogger:
    """Wraps stdlib logger to emit JSON-structured log lines."""

    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def _emit(self, level: int, message: str, **fields: Any) -> None:
        record = {"msg": message, **fields}
        self._logger.log(level, json.dumps(record))

    def info(self, message: str, **fields: Any) -> None:
        self._emit(logging.INFO, message, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._emit(logging.WARNING, message, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self._emit(logging.ERROR, message, **fields)

    def debug(self, message: str, **fields: Any) -> None:
        self._emit(logging.DEBUG, message, **fields)


def get_logger(name: str) -> StructuredLogger:
    """Return a structured logger for the given module name."""
    return StructuredLogger(name)
