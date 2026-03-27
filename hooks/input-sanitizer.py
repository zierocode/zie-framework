#!/usr/bin/env python3
"""PreToolUse hook — resolve relative file_path args and wrap risky Bash commands.

Two execution paths:
1. Write|Edit — resolves relative file_path to absolute; boundary-checks traversal.
2. Bash — matches risky-but-legitimate commands against CONFIRM_PATTERNS and wraps
   them in an interactive read -p confirmation prompt.

Both rewrites emit updatedInput + permissionDecision: "allow" so Claude never stalls.
Exits 0 on all error paths (ADR-003).
"""
import json
import os
import re
import shlex
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, read_event

# Bash commands that are legitimate but warrant interactive confirmation.
# MUST NOT overlap with safety-check.py BLOCKS — those are hard stops.
CONFIRM_PATTERNS = [
    r"rm\s+-rf\s+\./",        # rm -rf ./<path>  (project-relative recursive delete)
    r"rm\s+-f\s+\./",         # rm -f ./<path>   (project-relative force delete)
    r"git\s+clean\s+-fd",     # git clean -fd    (removes untracked files)
    r"make\s+clean",          # make clean       (may delete build artifacts)
    r"truncate\s+--size\s+0", # truncate --size 0 (zeroing a file)
]

# Operators that make a compound command unsafe to wrap in the confirmation prompt.
# Single | (pipe) is intentionally excluded — pipe chains are legitimate.
_DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\()')


def _is_safe_for_confirmation_wrapper(command: str) -> bool:
    """Return True if command can be safely embedded in the confirmation wrapper.

    Blocks commands containing compound operators (;, &&, ||, backtick, $())
    that could escape the {{ command; }} execution block.
    Single pipe (|) is permitted.
    """
    return not _DANGEROUS_COMPOUND_RE.search(command)

# ── Outer guard ──────────────────────────────────────────────────────────────
try:
    event = read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool_name not in {"Write", "Edit", "Bash"}:
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Write / Edit — relative path resolution ──────────────────────────────────
if tool_name in {"Write", "Edit"}:
    try:
        file_path = tool_input.get("file_path", "")
        if not file_path:
            sys.exit(0)

        p = Path(file_path)
        if p.is_absolute():
            sys.exit(0)

        cwd = get_cwd().resolve()
        abs_path = (cwd / p).resolve()

        # Boundary check — must stay inside project root.
        # Both sides are .resolve()-ed (symlinks followed) before is_relative_to()
        # comparison, which checks path components (not string prefix).
        if not abs_path.is_relative_to(cwd):
            print(
                f"[zie-framework] input-sanitizer: relative path escapes cwd,"
                f" skipping rewrite: {file_path}",
                file=sys.stderr,
            )
            sys.exit(0)

        updated = dict(tool_input)
        updated["file_path"] = str(abs_path)
        print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
        sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] input-sanitizer: {e}", file=sys.stderr)
        sys.exit(0)

# ── Bash — confirm-before-run rewrite ────────────────────────────────────────
if tool_name == "Bash":
    try:
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        # Skip already-wrapped commands to prevent double-wrapping on re-entrant calls.
        if "Would run:" in command:
            sys.exit(0)

        # preserve case — display only, not pattern matching (do NOT use normalize_command here)
        normalized = re.sub(r"\s+", " ", command.strip())

        for pattern in CONFIRM_PATTERNS:
            if re.search(pattern, normalized):
                if not _is_safe_for_confirmation_wrapper(command):
                    print(
                        "[zie-framework] input-sanitizer: compound command skipped confirmation wrap",
                        file=sys.stderr,
                    )
                    sys.exit(0)
                rewritten = (
                    f'printf "Would run: %s\\n" {shlex.quote(command)} '
                    f'&& read -p "Confirm? [y/N] " _y '
                    f'&& [ "$_y" = "y" ] && {{ {command}; }}'
                )
                updated = dict(tool_input)
                updated["command"] = rewritten
                print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
                sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] input-sanitizer: {e}", file=sys.stderr)
        sys.exit(0)
