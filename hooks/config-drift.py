#!/usr/bin/env python3
"""ConfigChange hook — detect CLAUDE.md / settings.json / zie-framework/.config drift.

Fires on ConfigChange events. Classifies the changed file and emits
additionalContext JSON instructing Claude to re-read the affected file
before continuing. Unrecognised paths exit silently.

Output protocol: JSON {"additionalContext": "..."} to stdout (same as
UserPromptSubmit hooks). Exit code is always 0 — hook never blocks Claude.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_error import log_error

# Outer guard ----------------------------------------------------------------
try:
    raw = sys.stdin.read()
    event = json.loads(raw)
except (json.JSONDecodeError, OSError):
    sys.exit(0)

try:
    if event.get("hook_event_name") != "ConfigChange":
        sys.exit(0)

    file_path = event.get("file_path", "")
    if not file_path:
        sys.exit(0)

    try:
        changed = Path(file_path)
    except (ValueError, OSError):
        sys.exit(0)

    cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))

    # -------------------------------------------------------------------------
    # Three-way classification (first match wins)
    # -------------------------------------------------------------------------

    # Branch A: CLAUDE.md — matches on filename alone (any depth)
    if changed.name == "CLAUDE.md":
        msg = (
            f"[zie-framework] CLAUDE.md has been updated on disk. "
            f"Re-read it now with Read('{file_path}') before continuing "
            f"so your instructions are current."
        )

    # Branch B: settings.json inside a .claude directory
    elif changed.name == "settings.json" and ".claude" in changed.parts:
        msg = (
            f"[zie-framework] .claude/settings.json has been updated on disk. "
            f"Re-read it now with Read('{file_path}') before continuing "
            f"so your permission rules are current."
        )

    # Branch C: .config under cwd/zie-framework/
    elif changed.name == ".config" and str(changed).startswith(str(cwd / "zie-framework")):
        msg = (
            "[zie-framework] zie-framework/.config has changed. "
            "Run /resync to reload project configuration before continuing."
        )

    # No match — unrelated config change, stay quiet
    else:
        sys.exit(0)

    print(json.dumps({"additionalContext": msg}))
    sys.exit(0)

except Exception as e:
    print(f"[zie-framework] config-drift: {e}", file=sys.stderr)
    sys.exit(0)
