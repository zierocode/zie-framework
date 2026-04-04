#!/usr/bin/env python3
"""PreToolUse:Write|Edit|Bash hook — unified safety check + input sanitization.

Execution order:
1. Write|Edit → relative path resolution (emits updatedInput + exit 0).
2. Bash → evaluate() first; if exit 2, stop. If exit 0, run confirm-wrap.
"""
import json
import os
import re
import shlex
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_safety import COMPILED_BLOCKS, COMPILED_WARNS, normalize_command
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path
from utils_config import load_config

# Bash commands that warrant interactive confirmation.
# Must NOT overlap with BLOCKS — those are hard stops.
CONFIRM_PATTERNS = [
    r"rm\s+-rf\s+\./",
    r"rm\s+-f\s+\./",
    r"git\s+clean\s+-fd",
    r"make\s+clean",
    r"truncate\s+--size\s+0",
]

_DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}])')


def _is_safe_for_confirmation_wrapper(command: str) -> bool:
    return not _DANGEROUS_COMPOUND_RE.search(command)


def evaluate(command: str) -> int:
    """Run regex evaluation. Returns 0 (allow) or 2 (block)."""
    cmd = normalize_command(command)
    for pattern, message in COMPILED_BLOCKS:
        if pattern.search(cmd):
            print(f"[zie-framework] BLOCKED: {message}")
            return 2
    for pattern, message in COMPILED_WARNS:
        if pattern.search(cmd):
            print(f"[zie-framework] WARNING: {message}")
    return 0


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
        if not abs_path.is_relative_to(cwd):
            print(
                f"[zie-framework] safety-check: relative path escapes cwd,"
                f" skipping rewrite: {file_path}",
                file=sys.stderr,
            )
            sys.exit(0)
        updated = dict(tool_input)
        updated["file_path"] = str(abs_path)
        print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
        sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] safety-check: {e}", file=sys.stderr)
        sys.exit(0)

# ── Bash — safety evaluate first, then confirm-wrap ──────────────────────────
if tool_name == "Bash":
    try:
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)
    except Exception:
        sys.exit(0)

    cwd = get_cwd()
    config = load_config(cwd)
    mode = config.get("safety_check_mode")

    if mode == "agent":
        sys.exit(0)

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

    if result == 2:
        sys.exit(2)  # blocked — sanitizer code unreachable

    # ── Bash confirm-wrap sanitizer ───────────────────────────────────────
    try:
        if "Would run:" in command:
            sys.exit(0)
        # preserve case — display only, not pattern matching
        # do not use normalize_command here (display-only normalization)
        normalized = re.sub(r"\s+", " ", command.strip())
        for pattern in CONFIRM_PATTERNS:
            if re.search(pattern, normalized):
                if not _is_safe_for_confirmation_wrapper(command):
                    print(
                        "[zie-framework] safety-check: compound command skipped confirmation wrap",
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
        print(f"[zie-framework] safety-check: {e}", file=sys.stderr)
        sys.exit(0)
