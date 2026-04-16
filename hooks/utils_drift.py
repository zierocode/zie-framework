#!/usr/bin/env python3
"""Drift log helpers — append, read count, close track."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils_error import log_error

_MAX_EVENTS = 200


def append_drift_event(cwd, event_dict: dict) -> None:
    """Append one NDJSON event to zie-framework/.drift-log.

    Trims log to last _MAX_EVENTS lines after write.
    Silently no-ops on any I/O error.
    """
    try:
        log_path = Path(cwd) / "zie-framework" / ".drift-log"
        line = json.dumps(event_dict, ensure_ascii=False)
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        _trim_log(log_path)
    except Exception as e:
        print(f"[zie-framework] utils_drift.append_drift_event: {e}", file=sys.stderr)


def read_drift_count(cwd) -> int:
    """Return number of events in .drift-log. Returns 0 on missing/unreadable file."""
    try:
        log_path = Path(cwd) / "zie-framework" / ".drift-log"
        if not log_path.exists():
            return 0
        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        return len(lines)
    except OSError as e:
        log_error("utils_drift", "read_drift_count", e)
        return 0


def close_drift_track(cwd, slug: str) -> None:
    """Set closed_at on the last open event matching slug.

    Rewrites the log file with the updated event.
    Silently no-ops on any error.
    """
    try:
        log_path = Path(cwd) / "zie-framework" / ".drift-log"
        if not log_path.exists():
            return
        raw_lines = log_path.read_text(encoding="utf-8").splitlines()
        events = []
        for raw in raw_lines:
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(json.loads(raw))
            except json.JSONDecodeError:
                events.append({"_raw": raw})

        for i in range(len(events) - 1, -1, -1):
            ev = events[i]
            if ev.get("slug") == slug and ev.get("closed_at") is None:
                events[i]["closed_at"] = datetime.now(timezone.utc).isoformat()
                break

        new_content = "\n".join(e.get("_raw", json.dumps(e, ensure_ascii=False)) for e in events) + "\n"
        log_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        print(f"[zie-framework] utils_drift.close_drift_track: {e}", file=sys.stderr)


def _trim_log(log_path: Path) -> None:
    """Keep only the last _MAX_EVENTS non-empty lines in log_path."""
    try:
        lines = [ln for ln in log_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) > _MAX_EVENTS:
            log_path.write_text("\n".join(lines[-_MAX_EVENTS:]) + "\n", encoding="utf-8")
    except OSError as e:
        log_error("utils_drift", "trim_log", e)
