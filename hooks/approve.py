#!/usr/bin/env python3
"""Approve a spec or plan file — sets approved:true + approved_at in frontmatter.

ONLY call this after the reviewer skill returns ✅ APPROVED.
The reviewer-gate hook blocks Write/Edit from setting approved:true directly,
so this script is the sole approval path.

Checks for a session marker written by subagent-stop.py when the reviewer
agent returns ✅ APPROVED. Warns (but does not block) if marker is absent.

Usage:
    python3 hooks/approve.py zie-framework/specs/YYYY-MM-DD-<slug>-design.md
    python3 hooks/approve.py zie-framework/plans/YYYY-MM-DD-<slug>.md
"""
import datetime
import os
import re
import sys
import tempfile
from pathlib import Path


def _reviewer_marker(file_path: str) -> Path:
    """Return the expected reviewer-pass marker path for this file."""
    kind = "spec" if "specs/" in file_path else "plan"
    project = Path(os.environ.get("CLAUDE_CWD", os.getcwd())).name
    safe = re.sub(r"[^a-zA-Z0-9]", "-", project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-reviewer-approved-{kind}"

_APPROVED_FALSE_RE = re.compile(r"^approved:\s*(false)?\s*$", re.MULTILINE)
_APPROVED_AT_BLANK_RE = re.compile(r"^approved_at:\s*$", re.MULTILINE)


def approve(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"approve.py: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    # Warn if reviewer-pass marker is absent (subagent-stop writes it on ✅ APPROVED)
    marker = _reviewer_marker(file_path)
    if not marker.exists():
        kind = "spec-reviewer" if "specs/" in file_path else "plan-reviewer"
        print(
            f"[approve.py] WARNING: no reviewer-pass marker found.\n"
            f"Run Skill('{kind}') first and wait for \u2705 APPROVED before approving.\n"
            f"Proceeding anyway — remove this file to re-gate: {marker}",
            file=sys.stderr,
        )

    content = path.read_text()
    today = datetime.date.today().isoformat()

    if not _APPROVED_FALSE_RE.search(content):
        print(f"approve.py: no 'approved: false' field in {file_path} — nothing to approve", file=sys.stderr)
        sys.exit(1)

    content = _APPROVED_FALSE_RE.sub("approved: true", content)
    content = _APPROVED_AT_BLANK_RE.sub(f"approved_at: {today}", content)

    path.write_text(content)
    print(f"\u2705 Approved: {file_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <spec-or-plan-file>", file=sys.stderr)
        sys.exit(1)
    approve(sys.argv[1])
