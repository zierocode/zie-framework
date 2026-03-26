#!/usr/bin/env python3
"""PostToolUseFailure hook — inject SDLC debug context on tool failure."""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import read_event, get_cwd, parse_roadmap_section_content, read_roadmap_cached

ALLOWED_TOOLS = {"Bash", "Write", "Edit"}

# ── Outer guard ──────────────────────────────────────────────────────────────

try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    if event.get("is_interrupt", False):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    if tool_name not in ALLOWED_TOOLS:
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Inner operations ─────────────────────────────────────────────────────────

try:
    cwd = get_cwd()
    session_id = event.get("session_id", "default")

    # ROADMAP Now lane (via session cache)
    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    try:
        roadmap_content = read_roadmap_cached(roadmap_path, session_id)
        now_items = parse_roadmap_section_content(roadmap_content, "now")
    except Exception:
        now_items = []
    active_task = now_items[0] if now_items else "(none — check ROADMAP Now lane)"

    # Git last commit
    try:
        log_result = subprocess.run(
            ["git", "log", "-1", "--pretty=%h %s"],
            capture_output=True, text=True, cwd=str(cwd), timeout=5,
        )
        last_commit = (
            log_result.stdout.strip()
            if log_result.returncode == 0
            else "(git unavailable)"
        )
    except Exception:
        last_commit = "(git unavailable)"

    # Git branch
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(cwd), timeout=5,
        )
        branch = (
            branch_result.stdout.strip()
            if branch_result.returncode == 0
            else "(git unavailable)"
        )
    except Exception:
        branch = "(git unavailable)"

    # Build context string
    context_string = (
        "[SDLC context at failure]\n"
        f"Active task: {active_task}\n"
        f"Branch: {branch}\n"
        f"Last commit: {last_commit}\n"
        "Quick fix: run `make test-unit` to reproduce; check output above for root cause."
    )

    print(json.dumps({"additionalContext": context_string}))

except Exception as e:
    print(f"[zie-framework] failure-context: {e}", file=sys.stderr)

sys.exit(0)
