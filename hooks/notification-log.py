#!/usr/bin/env python3
"""Notification hook — log permission_prompt and idle_prompt events.

Injects additionalContext when the same permission has been prompted
3 or more times in the current session.
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event, sanitize_log_field
from utils_io import project_tmp_path, safe_project_name, safe_write_tmp

# --- Outer guard: parse event; any failure exits 0 silently ---
try:
    event = read_event()
    notification_type = event.get("notification_type", "")
    if notification_type != "permission_prompt":
        sys.exit(0)
except Exception:
    sys.exit(0)


def _read_records(log_path):
    """Read newline-delimited JSON records from log_path.

    Returns [] if the file is absent or any line fails to parse (full reset).
    """
    if not log_path.exists():
        return []
    records = []
    try:
        for line in log_path.read_text().splitlines():
            line = line.strip()
            if line:
                records.append(json.loads(line))
    except Exception:
        return []
    return records


def _append_and_write(log_path, message):
    """Append a timestamped record to log_path and write atomically.

    Returns the updated records list (including the new entry).
    Logs to stderr if safe_write_tmp refuses the write.
    """
    records = _read_records(log_path)
    ts = datetime.now(timezone.utc).isoformat()
    records.append({"ts": ts, "msg": message})
    content = "\n".join(json.dumps(r) for r in records) + "\n"
    ok = safe_write_tmp(log_path, content)
    if not ok:
        print(
            f"[zie-framework] notification-log: failed to write {log_path}",
            file=sys.stderr,
        )
    return records


# --- Inner operations: file I/O; errors are logged, hook still exits 0 ---
try:
    message = sanitize_log_field(event.get("message", ""))
    project = safe_project_name(get_cwd().name)

    if notification_type == "permission_prompt":
        log_path = project_tmp_path("permission-log", project)
        records = _append_and_write(log_path, message)
        count = sum(1 for r in records if r.get("msg") == message)
        if count >= 3:
            print(json.dumps({
                "additionalContext": (
                    "This permission has been asked 3+ times this session. "
                    "Run /zie-permissions to add it to the allow list."
                )
            }))


except Exception as e:
    print(f"[zie-framework] notification-log: {e}", file=sys.stderr)
