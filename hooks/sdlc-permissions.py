#!/usr/bin/env python3
"""PermissionRequest:Bash hook — auto-approve safe SDLC operations."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import normalize_command, read_event

# Ordered allowlist.
# The metachar guard below blocks injection via &&, ||, ;, |, `, $(
# so argument-bearing commands like "git add ." and "make test-unit" are safe.
SAFE_PATTERNS = [
    r"git add\b",
    r"git commit\b",
    r"git diff\b",
    r"git status\b",
    r"git log\b",
    r"git stash\b",
    r"make test\b",
    r"make lint\b",
    r"python3 -m pytest\b",
    r"python3 -m bandit\b",
]

# Reject any command containing shell metacharacters — no quote-aware parsing needed
_METACHARS = (";", "&&", "||", "|", "`", "$(")


# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)
    command = (event.get("tool_input") or {}).get("command", "")
    if not command:
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Inner operations ──────────────────────────────────────────────────────────

try:
    cmd = normalize_command(command)

    if any(mc in cmd for mc in _METACHARS):
        sys.exit(0)

    matched_pattern = None
    for pattern in SAFE_PATTERNS:
        if re.match(pattern, cmd):
            matched_pattern = pattern
            break

    if matched_pattern:
        decision = {
            "decision": {
                "behavior": "allow",
                "updatedPermissions": {
                    "destination": "session",
                    "permissions": [
                        {"tool": "Bash", "command": matched_pattern}
                    ],
                },
            }
        }
        print(json.dumps(decision))

except Exception as e:
    print(f"[zie-framework] sdlc-permissions: {e}", file=sys.stderr)

sys.exit(0)
