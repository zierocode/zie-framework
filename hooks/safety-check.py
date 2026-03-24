#!/usr/bin/env python3
"""PreToolUse:Bash hook — block destructive commands and enforce git workflow."""
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from utils import BLOCKS, get_cwd, load_config, normalize_command, project_tmp_path, read_event, safe_project_name, WARNS


def evaluate(command: str) -> int:
    """Run regex evaluation. Returns 0 (allow) or 2 (block)."""
    cmd = normalize_command(command)

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
