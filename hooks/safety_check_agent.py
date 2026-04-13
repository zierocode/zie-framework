#!/usr/bin/env python3
"""AI-powered safety check using a Claude subagent.

This module is imported by safety-check.py for agent-mode dispatch.
It is NOT registered as a standalone hook in hooks.json.
Run directly only for manual testing: python3 safety_check_agent.py

Named with underscores (safety_check_agent.py) to allow Python importlib
to load it cleanly from tests and other hooks.
"""
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_safety import BLOCKS, COMPILED_BLOCKS, normalize_command
from utils_event import get_cwd, read_event
from utils_config import load_config

MAX_CMD_CHARS = 4096

# Agent-specific additions beyond the shared BLOCKS list — pre-compiled for performance
import re as _re
_AGENT_EXTRA_BLOCKS = [
    (_re.compile(r"curl\s+.*\|\s*bash\b", _re.IGNORECASE), "curl pipe to bash blocked — potential code injection"),
    (_re.compile(r"curl\s+.*\|\s*sh\b", _re.IGNORECASE), "curl pipe to sh blocked — potential code injection"),
    (_re.compile(r"wget\s+.*\|\s*bash\b", _re.IGNORECASE), "wget pipe to bash blocked — potential code injection"),
    (_re.compile(r"wget\s+.*\|\s*sh\b", _re.IGNORECASE), "wget pipe to sh blocked — potential code injection"),
]
_COMPILED_AGENT_BLOCKS = COMPILED_BLOCKS + _AGENT_EXTRA_BLOCKS

_MODEL_UNAVAILABLE_SUBSTRINGS = [
    "issue with the selected model",
    "may not exist or you may not have access",
    "run --model to pick",
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
    for pattern, message in _COMPILED_AGENT_BLOCKS:
        if pattern.search(cmd):
            print(f"[zie-framework] BLOCKED: {message}")
            return 2
    return 0


def _check_claude_cli_exists() -> bool:
    """Check if the claude CLI is available on PATH."""
    return shutil.which("claude") is not None


def invoke_subagent(command: str, timeout: int = 30) -> str:
    """Call claude CLI to evaluate the command. Returns agent response text."""
    if not _check_claude_cli_exists():
        print(
            "[zie-framework] safety_check_agent: claude CLI not found, "
            "falling back to regex mode",
            file=sys.stderr,
        )
        raise RuntimeError("claude CLI not found")

    if len(command) > MAX_CMD_CHARS:
        command = command[:MAX_CMD_CHARS] + "\n[... truncated]"
    # XML-delimit command content to prevent prompt injection via shell command strings
    # Escape both opening and closing tags symmetrically; also strip Unicode direction overrides
    safe_command = command.replace("<command>", "<\\/command-tag>")
    safe_command = safe_command.replace("</command>", "<\\/command>")
    # Strip Unicode bidirectional override characters (common prompt injection vector)
    for char in ("\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069"):
        safe_command = safe_command.replace(char, "")
    prompt = (
        "You are a safety agent for a developer terminal. "
        "Evaluate whether this shell command is safe to run:\n\n"
        f"<command>\n{safe_command}\n</command>\n\n"
        "Reply with exactly one word: ALLOW (if safe) or BLOCK (if dangerous)."
    )
    _model = os.environ.get("ANTHROPIC_DEFAULT_HAIKU_MODEL", "claude-haiku-4-5-20251001")
    result = subprocess.run(
        ["claude", "--print", "--model", _model, prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    # Detect model-unavailable: check returncode + stdout/stderr for error indicators
    if result.returncode != 0:
        combined = (result.stdout + result.stderr).lower()
        if any(s in combined for s in _MODEL_UNAVAILABLE_SUBSTRINGS):
            raise RuntimeError("model unavailable — falling back to regex")
    return result.stdout.strip()


def evaluate(command: str, mode: str, timeout: int = 30) -> int:
    """Evaluate command via agent with regex fallback. Returns 0 (allow) or 2 (block)."""
    # Check if claude CLI exists first - if not, skip agent mode entirely
    if not _check_claude_cli_exists():
        print(
            "[zie-framework] safety_check_agent: claude CLI not found, "
            "skipping agent mode — using regex only",
            file=sys.stderr,
        )
        return _regex_evaluate(command)

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
