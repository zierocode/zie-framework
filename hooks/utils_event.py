#!/usr/bin/env python3
"""Hook event I/O and session utilities for zie-framework hooks."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

from utils_error import log_error


def read_event() -> dict:
    """Read and parse the hook event from stdin.

    Exits with code 0 on any parse failure — hooks must never crash.
    """
    try:
        return json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        sys.exit(0)


def get_cwd() -> Path:
    """Return the working directory for the current Claude Code session.

    Prefers CLAUDE_CWD env var (set by Claude Code) over os.getcwd().
    """
    return Path(os.environ.get("CLAUDE_CWD", os.getcwd()))


def sanitize_log_field(value: object, max_len: int = 10240) -> str:
    """Strip ASCII control characters and enforce length cap on a log field value.

    Converts value to str first, truncates to max_len bytes, then replaces
    chars in range 0x00-0x1f and 0x7f with '?' to prevent log injection
    and disk exhaustion from unbounded event-controlled input.
    """
    s = str(value)
    if len(s) > max_len:
        s = s[:max_len]
    return re.sub(r"[\x00-\x1f\x7f]", "?", s)


def log_hook_timing(
    hook_name: str,
    duration_ms: int,
    exit_code: int,
    session_id: str | None = None,
) -> None:
    """Append a JSON timing entry to the session timing log.

    No-op when session_id is empty or None. Never raises.
    """
    if not session_id:
        return
    try:
        from datetime import datetime, timezone

        safe_id = re.sub(r"[^a-zA-Z0-9_-]", "-", session_id)
        log_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
        log_dir.mkdir(parents=True, exist_ok=True)
        entry = json.dumps(
            {
                "hook": hook_name,
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "ts": datetime.now(timezone.utc).isoformat(),
            }
        )
        with open(log_dir / "timing.log", "a") as f:
            f.write(entry + "\n")
    except OSError as e:
        log_error("utils_event", "log_hook_timing", e)


def call_zie_memory_api(url: str, key: str, endpoint: str, payload: dict, timeout: int = 5) -> None:
    """POST payload as JSON to a zie-memory API endpoint. Re-raises on network error.

    Caller is responsible for URL validation (must be https://) and error handling.
    """
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{url}{endpoint}",
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    urllib.request.urlopen(req, timeout=timeout)  # nosec B310 — URL built from hardcoded zie-memory API base, not user input
