"""Verify no hook file has config.get() calls with inline default arguments."""

import re
from pathlib import Path

HOOKS_DIR = Path(__file__).parents[2] / "hooks"
HOOK_FILES = [
    "auto-test.py",
    "task-completed-gate.py",
    "session-resume.py",
    "safety-check.py",
    "safety_check_agent.py",
]


def test_no_inline_config_defaults():
    """config.get() calls must not pass a second default argument.

    CONFIG_DEFAULTS in utils.py is the single source of truth; inline defaults
    are redundant and risk diverging.
    """
    pattern = re.compile(r'config\.get\(["\']([^"\']+)["\']\s*,\s*[^)]+\)')
    violations = []
    for filename in HOOK_FILES:
        content = (HOOKS_DIR / filename).read_text()
        for lineno, line in enumerate(content.splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{filename}:{lineno}: {line.strip()}")
    assert not violations, (
        "Inline config.get() defaults found — remove second arg, rely on CONFIG_DEFAULTS:\n" + "\n".join(violations)
    )
