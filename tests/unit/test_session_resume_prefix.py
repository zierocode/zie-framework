"""Regression test: no bare [zie] log prefix in any hook file."""
import re
from pathlib import Path

HOOKS_DIR = Path(__file__).parents[2] / "hooks"


def test_no_bare_zie_prefix_in_hooks():
    """No hook file may use bare [zie] log prefix — must be [zie-framework]."""
    violations = []
    pattern = re.compile(r'\[zie\]')  # bare [zie] only, not [zie-framework]
    for hook_py in HOOKS_DIR.glob("*.py"):
        text = hook_py.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{hook_py.name}:{lineno}: {line.strip()}")
    assert not violations, (
        f"Bare [zie] log prefix found (use [zie-framework] instead):\n"
        + "\n".join(violations)
    )
