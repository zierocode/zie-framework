#!/usr/bin/env python3
"""Stop hook — block if uncommitted implementation files are detected.

Emits {"decision": "block", "reason": "..."} to stdout when git status
reports uncommitted hooks/*.py, tests/*.py, commands/*.md, skills/**/*.md,
or templates/**/* files. Exits 0 on all error paths (ADR-003).

Infinite-loop guard: if event["stop_hook_active"] is truthy, the hook
has already fired once for this continuation cycle — exit immediately
without running git, preventing Claude from being blocked indefinitely.
"""
import fnmatch
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import read_event, get_cwd

# Canonical implementation file patterns for zie-framework layout.
# Paths are matched against the raw path token from `git status --short`
# (relative to repo root, e.g. "hooks/stop-guard.py").
IMPL_PATTERNS = [
    "hooks/*.py",
    "tests/*.py",
    "commands/*.md",
    "skills/*.md",
    "skills/*/*.md",
    "templates/*",
    "templates/*/*",
    "templates/*/*/*",
]

# ---------------------------------------------------------------------------
# Outer guard — parse stdin; never block Claude on failure
# ---------------------------------------------------------------------------
try:
    event = read_event()
    # Infinite-loop guard: Claude Code sets stop_hook_active on the Stop event
    # that follows a hook-triggered continuation. Exit immediately so the guard
    # fires at most once per original response.
    if event.get("stop_hook_active"):
        sys.exit(0)
except Exception:
    sys.exit(0)

# ---------------------------------------------------------------------------
# Inner operations — git status + filter
# ---------------------------------------------------------------------------
try:
    cwd = get_cwd()
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=5,
    )
    # Non-zero return code means not a git repo, detached HEAD, or bare repo.
    if result.returncode != 0:
        sys.exit(0)

    uncommitted = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        # git status --short format: XY<space>path
        # XY is two chars; char index 0=staged, 1=unstaged; path starts at [3:]
        path_token = line[3:].strip()
        # Strip rename arrows: "old -> new" — take the destination
        if " -> " in path_token:
            path_token = path_token.split(" -> ", 1)[1].strip()
        if any(fnmatch.fnmatch(path_token, pat) for pat in IMPL_PATTERNS):
            uncommitted.append(path_token)

    if not uncommitted:
        sys.exit(0)

    file_list = "\n".join(f"  {p}" for p in sorted(uncommitted))
    reason = (
        f"Uncommitted implementation files detected:\n{file_list}\n\n"
        "Commit this work before ending:\n"
        "  git add -A && git commit -m 'feat: <describe change>'"
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)

except Exception as e:
    print(f"[zie-framework] stop-guard: {e}", file=sys.stderr)
    sys.exit(0)
