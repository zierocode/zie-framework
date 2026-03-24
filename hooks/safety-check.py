#!/usr/bin/env python3
"""PreToolUse:Bash hook — block destructive commands and enforce git workflow."""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, load_config, project_tmp_path, read_event, safe_project_name

BLOCKS = [
    # Filesystem destruction
    (r"rm\s+-rf\s+(/\s|/\b|/$)", "rm -rf / is blocked — this would destroy the system"),
    (r"rm\s+-rf\s+~", "rm -rf ~ is blocked — this would destroy your home directory"),
    (r"rm\s+-rf\s+\.", "rm -rf . blocked — use explicit paths"),

    # Database destruction
    (r"\bdrop\s+database\b", "DROP DATABASE blocked — use migrations to remove databases"),
    (r"\bdrop\s+table\b", "DROP TABLE blocked — use alembic/migrations for schema changes"),
    (r"\btruncate\s+table\b", "TRUNCATE TABLE blocked — be explicit with user before truncating"),

    # Force push
    (r"git\s+push\s+.*--force\b", "Force push blocked — use 'git push' normally or ask Zie explicitly"),
    (r"git\s+push\s+.*-f\b", "Force push blocked — use 'git push' normally"),
    (r"git\s+push\s+.*origin\s+main\b", "Direct push to main blocked — use 'make ship' instead"),
    (r"git\s+push\s+.*origin\s+master\b", "Direct push to master blocked — use 'make ship' instead"),

    # Hard reset
    (r"git\s+reset\s+--hard\b", "git reset --hard blocked — this discards uncommitted work. Use 'git stash' instead"),

    # Skip hooks
    (r"--no-verify\b", "--no-verify blocked — hooks exist for a reason. Fix the hook failure instead"),
]

# WARNS: non-blocking notices. Do NOT add patterns already caught by BLOCKS above.
WARNS = [
    (r"docker\s+compose\s+down\s+.*--volumes\b",
     "docker compose down --volumes will delete DB data — make sure you have a backup"),
    (r"alembic\s+downgrade\b",
     "Alembic downgrade detected — verify this won't lose production data"),
]


def evaluate(command: str) -> int:
    """Run regex evaluation. Returns 0 (allow) or 2 (block)."""
    cmd = re.sub(r'\s+', ' ', command.strip().lower())

    for pattern, message in BLOCKS:
        if re.search(pattern, cmd):
            print(f"[zie-framework] BLOCKED: {message}")
            return 2

    for pattern, message in WARNS:
        if re.search(pattern, cmd):
            print(f"[zie-framework] WARNING: {message}")

    return 0


if __name__ == "__main__":
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

    cwd = get_cwd()
    config = load_config(cwd)
    mode = config.get("safety_check_mode", "regex")

    if mode == "agent":
        sys.exit(0)  # defer entirely to safety-check-agent hook

    result = evaluate(command)

    if mode == "both":
        try:
            log_path = project_tmp_path("safety-ab", cwd.name)
            record = {
                "ts": time.time(),
                "command": command,
                "agent": "regex",
                "agent_reason": "blocked" if result == 2 else "allowed",
            }
            with open(log_path, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[zie-framework] safety-check: A/B log write failed: {e}", file=sys.stderr)

    sys.exit(result)
