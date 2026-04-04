#!/usr/bin/env python3
"""Safety pattern constants and command normalization for zie-framework hooks."""
import re

BLOCKS = [
    # Filesystem destruction
    (r"rm\s+-rf\s+(/\s|/\b|/$)", "rm -rf / is blocked — this would destroy the system"),
    (r"rm\s+-rf\s+~", "rm -rf ~ is blocked — this would destroy your home directory"),
    (r"rm\s+-rf\s+\.(?!/\S)", "rm -rf . blocked — use explicit paths"),
    # Database destruction
    (r"\bdrop\s+database\b", "DROP DATABASE blocked — use migrations to remove databases"),
    (r"\bdrop\s+table\b", "DROP TABLE blocked — use alembic/migrations for schema changes"),
    (r"\btruncate\s+table\b", "TRUNCATE TABLE blocked — be explicit with user before truncating"),
    # Force push
    (r"git\s+push\s+.*--force\b", "Force push blocked — use 'git push' normally or ask Zie explicitly"),
    (r"git\s+push\s+.*-f\b", "Force push blocked — use 'git push' normally"),
    (r"git\s+push\b(?!.*--tags).*\borigin\s+main\b", "Direct push to main blocked — use 'make release NEW=x.y.z' instead"),
    (r"git\s+push\b(?!.*--tags).*\borigin\s+master\b", "Direct push to master blocked — use 'make release NEW=x.y.z' instead"),
    # Hard reset
    (r"git\s+reset\s+--hard\b", "git reset --hard blocked — this discards uncommitted work. Use 'git stash' instead"),
    # Skip hooks
    (r"--no-verify\b", "--no-verify blocked — hooks exist for a reason. Fix the hook failure instead"),
]

# Non-blocking notices. Do NOT add patterns already caught by BLOCKS above.
WARNS = [
    (r"docker\s+compose\s+down\s+.*--volumes\b",
     "docker compose down --volumes will delete DB data — make sure you have a backup"),
    (r"alembic\s+downgrade\b",
     "Alembic downgrade detected — verify this won't lose production data"),
]

# Compiled once at import time — use these in hot-path hooks instead of re.search(string, ...)
COMPILED_BLOCKS = [(re.compile(p, re.IGNORECASE), msg) for p, msg in BLOCKS]
COMPILED_WARNS  = [(re.compile(p, re.IGNORECASE), msg) for p, msg in WARNS]


def normalize_command(cmd: str) -> str:
    """Normalize whitespace and lowercase a shell command for pattern matching."""
    return re.sub(r'\s+', ' ', cmd.strip().lower())
