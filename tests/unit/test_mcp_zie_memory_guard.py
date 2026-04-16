"""Structural tests: commands that call zie-memory MCP tools must guard with zie_memory_enabled."""

import re
from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"

MCP_PATTERN = re.compile(r"mcp__plugin_zie.memory_zie.memory__\w+")


def _has_unguarded_mcp(text: str) -> list[int]:
    """Return line numbers where mcp zie-memory calls appear without zie_memory_enabled guard."""
    lines = text.splitlines()
    violations = []
    for i, line in enumerate(lines, 1):
        if MCP_PATTERN.search(line):
            # Look back up to 5 lines for a zie_memory_enabled guard
            context = " ".join(lines[max(0, i - 6) : i])
            if "zie_memory_enabled" not in context:
                violations.append(i)
    return violations


def test_backlog_brain_calls_guarded():
    text = (COMMANDS_DIR / "backlog.md").read_text()
    violations = _has_unguarded_mcp(text)
    assert not violations, (
        f"backlog.md: unguarded zie-memory calls at lines {violations} — wrap with if zie_memory_enabled=true"
    )


def test_plan_brain_calls_guarded():
    text = (COMMANDS_DIR / "plan.md").read_text()
    violations = _has_unguarded_mcp(text)
    assert not violations, f"plan.md: unguarded zie-memory calls at lines {violations}"


def test_implement_brain_calls_guarded():
    text = (COMMANDS_DIR / "implement.md").read_text()
    violations = _has_unguarded_mcp(text)
    assert not violations, f"implement.md: unguarded zie-memory calls at lines {violations}"


def test_retro_brain_calls_guarded():
    text = (COMMANDS_DIR / "retro.md").read_text()
    violations = _has_unguarded_mcp(text)
    assert not violations, f"retro.md: unguarded zie-memory calls at lines {violations}"


def test_fix_brain_calls_guarded():
    text = (COMMANDS_DIR / "fix.md").read_text()
    violations = _has_unguarded_mcp(text)
    assert not violations, f"fix.md: unguarded zie-memory calls at lines {violations}"


def test_release_brain_calls_guarded():
    text = (COMMANDS_DIR / "release.md").read_text()
    violations = _has_unguarded_mcp(text)
    assert not violations, f"release.md: unguarded zie-memory calls at lines {violations}"
