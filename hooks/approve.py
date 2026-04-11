#!/usr/bin/env python3
"""Approve a spec or plan file — sets approved:true + approved_at in frontmatter.

ONLY call this after the reviewer skill returns ✅ APPROVED.
The reviewer-gate hook blocks Write/Edit from setting approved:true directly,
so this script is the sole approval path.

Usage:
    python3 hooks/approve.py zie-framework/specs/YYYY-MM-DD-<slug>-design.md
    python3 hooks/approve.py zie-framework/plans/YYYY-MM-DD-<slug>.md
"""
import datetime
import re
import sys
from pathlib import Path

_APPROVED_FALSE_RE = re.compile(r"^approved:\s*(false)?\s*$", re.MULTILINE)
_APPROVED_AT_BLANK_RE = re.compile(r"^approved_at:\s*$", re.MULTILINE)


def approve(file_path: str) -> None:
    path = Path(file_path)
    if not path.exists():
        print(f"approve.py: file not found: {file_path}", file=sys.stderr)
        sys.exit(1)

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
