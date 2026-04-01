#!/usr/bin/env python3
"""PreToolUse:Bash hook — AI-powered safety check using a Claude subagent.

Named with underscores (safety_check_agent.py) to allow Python importlib
to load it cleanly from tests and other hooks.
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import BLOCKS, get_cwd, load_config, normalize_command, read_event

MAX_CMD_CHARS = 4096

# Agent-specific additions beyond the shared BLOCKS list
_AGENT_BLOCKS = BLOCKS + [
    (r"curl\s+.*\|\s*bash\b", "curl pipe to bash blocked — potential code injection"),
    (r"curl\s+.*\|\s*sh\b", "curl pipe to sh blocked — potential code injection"),
    (r"wget\s+.*\|\s*bash\b", "wget pipe to bash blocked — potential code injection"),
    (r"wget\s+.*\|\s*sh\b", "wget pipe to sh blocked — potential code injection"),
]


def parse_agent_response(text: str) -> str:
    """Extract ALLOW or BLOCK from agent response text. BLOCK takes precedence."""
    has_block = "BLOCK" in text
    has_allow = "ALLOW" in text
    if has_block:
        return "BLOCK"
    if has_allow:
        return "ALLOW"
    return "ALLOW"  # default: allow on ambiguity


def _regex_evaluate(command: str) -> int:
    """Regex safety check used as fallback when agent is unavailable."""
    cmd = normalize_command(command)
    for pattern, message in _AGENT_BLOCKS:
        if re.search(pattern, cmd):
            print(f"[zie-framework] BLOCKED: {message}")
            return 2
    return 0


def invoke_subagent(command: str, timeout: int = 30) -> str:
    """Call claude CLI to evaluate the command. Returns agent response text."""
    if len(command) > MAX_CMD_CHARS:
        command = command[:MAX_CMD_CHARS] + "\n[... truncated]"
    prompt = (
        "You are a safety agent for a developer terminal. "
        "Evaluate whether this shell command is safe to run:\n\n"
        f"```\n{command}\n```\n\n"
        "Reply with exactly one word: ALLOW (if safe) or BLOCK (if dangerous)."
    )
    result = subprocess.run(
        ["claude", "--print", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.stdout.strip()


def evaluate(command: str, mode: str, timeout: int = 30) -> int:
    """Evaluate command via agent with regex fallback. Returns 0 (allow) or 2 (block)."""
    try:
        response = invoke_subagent(command, timeout=timeout)
        decision = parse_agent_response(response)
        return 2 if decision == "BLOCK" else 0
    except Exception as e:
        print(
            f"[zie-framework] safety_check_agent: agent error, falling back to regex: {e}",
            file=sys.stderr,
        )
        return _regex_evaluate(command)


if __name__ == "__main__":
    try:
        event = read_event()

        tool_name = event.get("tool_name", "")
        if tool_name != "Bash":
            sys.exit(0)

        command = (event.get("tool_input") or {}).get("command", "")
        if not command:
            sys.exit(0)

        cwd = get_cwd()
        config = load_config(cwd)
        mode = config.get("safety_check_mode")

        if mode not in ("agent", "both"):
            sys.exit(0)  # defer to safety-check.py in regex mode

        result = evaluate(command, mode, timeout=config["safety_agent_timeout_s"])
        sys.exit(result)
    except Exception:
        sys.exit(0)
