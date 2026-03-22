#!/usr/bin/env python3
"""PreToolUse:Bash hook — block destructive commands and enforce git workflow."""
import sys
import json
import re

try:
    event = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

tool_name = event.get("tool_name", "")
if tool_name != "Bash":
    sys.exit(0)

command = (event.get("tool_input") or {}).get("command", "")
if not command:
    sys.exit(0)

cmd = command.strip().lower()

BLOCKS = [
    # Filesystem destruction
    (r"rm\s+-rf\s+/\b", "rm -rf / is blocked — this would destroy the system"),
    (r"rm\s+-rf\s+~\b", "rm -rf ~ is blocked — this would destroy your home directory"),
    (r"rm\s+-rf\s+\.", "rm -rf . blocked — use explicit paths"),

    # Database destruction
    (r"\bdrop\s+database\b", "DROP DATABASE blocked — use migrations to remove databases"),
    (r"\bdrop\s+table\b", "DROP TABLE blocked — use alembic/migrations for schema changes"),
    (r"\btruncate\s+table\b", "TRUNCATE TABLE blocked — be explicit with user before truncating"),

    # Force push
    (r"git\s+push\s+.*--force\b", "Force push blocked — use 'git push' normally or ask Zie explicitly"),
    (r"git\s+push\s+.*-f\b", "Force push blocked — use 'git push' normally"),
    (r"git\s+push\s+origin\s+main\b", "Direct push to main blocked — use 'make ship' instead"),
    (r"git\s+push\s+origin\s+master\b", "Direct push to master blocked — use 'make ship' instead"),

    # Hard reset
    (r"git\s+reset\s+--hard\b", "git reset --hard blocked — this discards uncommitted work. Use 'git stash' instead"),

    # Skip hooks
    (r"--no-verify\b", "--no-verify blocked — hooks exist for a reason. Fix the hook failure instead"),
]

WARNS = [
    (r"git\s+push\s+.*--force-with-lease\b",
     "Force-with-lease detected — make sure this is intentional"),
    (r"docker\s+compose\s+down\s+.*--volumes\b",
     "docker compose down --volumes will delete DB data — make sure you have a backup"),
    (r"alembic\s+downgrade\b",
     "Alembic downgrade detected — verify this won't lose production data"),
]

# Check blocks
for pattern, message in BLOCKS:
    if re.search(pattern, cmd):
        print(f"[zie-framework] BLOCKED: {message}")
        sys.exit(1)  # Non-zero exit blocks the tool call (if Claude Code honors it)

# Check warns (non-blocking)
for pattern, message in WARNS:
    if re.search(pattern, cmd):
        print(f"[zie-framework] WARNING: {message}")
