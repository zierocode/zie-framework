#!/usr/bin/env python3
"""SubagentStop hook — append completed subagent metadata to a JSONL log.

Registered as async: true. Never blocks Claude.
Two-tier error handling per zie-framework hook convention:
  Tier 1 (outer guard): parse + project check — bare except → sys.exit(0)
  Tier 2 (inner ops):   file I/O — except Exception as e → stderr + exit(0)
"""
import fcntl
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils_event import get_cwd, read_event
from utils_io import atomic_write, project_tmp_path

# --- Tier 1: outer guard ---------------------------------------------------
try:
    event = read_event()
    cwd = get_cwd()
    if not (cwd / "zie-framework").is_dir():
        sys.exit(0)
except Exception:
    sys.exit(0)

# --- Tier 2: inner operations ---------------------------------------------
try:
    agent_id = event.get("agent_id", "unknown")
    agent_type = event.get("agent_type", "unknown")
    raw_msg = event.get("last_assistant_message")
    last_message = str(raw_msg or "")[:500]

    # Write a session marker when a reviewer agent returns ✅ APPROVED.
    # approve.py reads these markers to confirm the reviewer ran.
    _REVIEWER_KINDS = {"spec-reviewer": "spec", "plan-reviewer": "plan"}
    if agent_type in _REVIEWER_KINDS and "\u2705 APPROVED" in last_message:
        kind = _REVIEWER_KINDS[agent_type]
        marker = project_tmp_path(f"reviewer-approved-{kind}", cwd.name)
        try:
            marker.write_text("approved")
        except Exception:
            pass  # never block on marker write failure

    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "agent_id": agent_id,
        "agent_type": agent_type,
        "last_message": last_message,
    }

    log_path = project_tmp_path("subagent-log", cwd.name)

    if os.path.islink(log_path):
        print(
            f"[zie-framework] subagent-stop: log path is a symlink,"
            f" skipping write: {log_path}",
            file=sys.stderr,
        )
        sys.exit(0)

    lock_path = Path(str(log_path) + ".lock")
    with open(lock_path, "w") as lock_fh:
        fcntl.flock(lock_fh, fcntl.LOCK_EX)
        existing = ""
        if os.path.exists(log_path):
            with open(log_path) as fh:
                existing = fh.read()
        atomic_write(log_path, existing + json.dumps(record) + "\n")
        fcntl.flock(lock_fh, fcntl.LOCK_UN)

except Exception as e:
    print(f"[zie-framework] subagent-stop: {e}", file=sys.stderr)

sys.exit(0)
