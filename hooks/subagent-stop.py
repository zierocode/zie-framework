#!/usr/bin/env python3
"""SubagentStop hook — append completed subagent metadata to a JSONL log.

Registered as async: true. Never blocks Claude.
Two-tier error handling per zie-framework hook convention:
  Tier 1 (outer guard): parse + project check — bare except → sys.exit(0)
  Tier 2 (inner ops):   file I/O — except Exception as e → stderr + exit(0)
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import get_cwd, project_tmp_path, read_event

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

    with open(log_path, "a") as fh:
        fh.write(json.dumps(record) + "\n")

except Exception as e:
    print(f"[zie-framework] subagent-stop: {e}", file=sys.stderr)

sys.exit(0)
