#!/usr/bin/env python3
"""PreToolUse Write|Edit hook — block direct approved:true writes to spec/plan files.

Prevents Claude from self-approving specs and plans without running the
reviewer loop. The only way to set approved:true is via:

    python3 hooks/approve.py <file>

called through the Bash tool AFTER the reviewer returns ✅ APPROVED.

Exits:
  0 — not a spec/plan file, or already approved → allow
  2 — spec/plan transitioning to approved:true via Write/Edit → block
  0 — any error → graceful degradation, always allow
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_error import log_error
from utils_event import get_cwd, read_event

_APPROVED_TRUE_RE = re.compile(r"^approved:\s*true\s*$", re.MULTILINE)


def _is_spec_or_plan(file_path: str) -> bool:
    p = Path(file_path).as_posix()
    return "zie-framework/specs/" in p or "zie-framework/plans/" in p


def _already_approved(full_path: Path) -> bool:
    """True if file already has approved:true — allow idempotent re-writes."""
    try:
        return bool(_APPROVED_TRUE_RE.search(full_path.read_text()))
    except (OSError, FileNotFoundError) as e:
        log_error("reviewer-gate", "read_file", e)
        return False


try:
    event = read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool_name not in {"Write", "Edit"}:
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path or not _is_spec_or_plan(file_path):
        sys.exit(0)

    content = tool_input.get("content", "") if tool_name == "Write" else tool_input.get("new_string", "")
    if not _APPROVED_TRUE_RE.search(content):
        sys.exit(0)

    cwd = get_cwd()
    full_path = Path(file_path) if Path(file_path).is_absolute() else cwd / file_path
    if _already_approved(full_path):
        sys.exit(0)  # idempotent — already approved

    kind = "spec" if "specs/" in file_path else "plan"
    skill = "zie-framework:spec-review" if kind == "spec" else "zie-framework:plan-review"

    print(
        f"[reviewer-gate] BLOCKED: Cannot self-approve {kind}.\n"
        f"\n"
        f"Step 1 — run the reviewer:\n"
        f"  Skill('{skill}')\n"
        f"\n"
        f"Step 2 — after reviewer returns \u2705 APPROVED, set approval via Bash:\n"
        f"  python3 hooks/approve.py {file_path}\n"
        f"\n"
        f"Writing approved:true directly is always blocked."
    )
    sys.exit(2)

except Exception as e:
    print(f"[reviewer-gate] error: {e}", file=sys.stderr)
    sys.exit(0)
