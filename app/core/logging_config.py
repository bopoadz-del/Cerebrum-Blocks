"""Structured logging + optional Sentry initialization.

Call configure_logging() and init_sentry() once at app startup, before any
loggers emit records. Both are idempotent and safe to call when the env vars
they depend on are unset.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from typing import Any


_RESERVED_LOGRECORD_ATTRS = {
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
}


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record. Includes any `extra={}` fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Surface caller-supplied extras
        for k, v in record.__dict__.items():
            if k in _RESERVED_LOGRECORD_ATTRS or k.startswith("_"):
                continue
            payload[k] = v
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure root logger. JSON in prod, plain text in dev.

    Honors LOG_LEVEL (default INFO) and LOG_FORMAT (json|text, default json
    in prod, text in dev).
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    env = os.getenv("ENV", os.getenv("ENVIRONMENT", "production")).strip().lower()
    is_dev = env in {"dev", "development", "local", "test", "testing"}
    fmt = os.getenv("LOG_FORMAT", "text" if is_dev else "json").lower()

    handler = logging.StreamHandler(sys.stdout)
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
        )

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)

    # Tame noisy third-party loggers without losing errors
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))


def init_sentry() -> bool:
    """Initialize Sentry if SENTRY_DSN is set and sentry_sdk is installed.

    Returns True on success, False otherwise. Never raises.
    """
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
    except ImportError:
        logging.getLogger(__name__).warning(
            "SENTRY_DSN set but sentry-sdk not installed; skipping Sentry init"
        )
        return False

    env = os.getenv("ENV", os.getenv("ENVIRONMENT", "production")).strip().lower()
    sentry_sdk.init(
        dsn=dsn,
        environment=env,
        release=os.getenv("RELEASE_SHA") or None,
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    return True
