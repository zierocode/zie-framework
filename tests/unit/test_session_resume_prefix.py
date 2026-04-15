"""Regression test: no bare [zie] log prefix in any hook file."""
import re
from pathlib import Path

HOOKS_DIR = Path(__file__).parents[2] / "hooks"

# Valid prefixes: [zie-framework] (full) or [zf] (compact)
_VALID_PREFIX_RE = re.compile(r'\[(zie-framework|zf)\]')
# Bare [zie] without -framework or f suffix
_BARE_ZIE_RE = re.compile(r'\[zie\](?![\w-])')


def test_no_bare_zie_prefix_in_hooks():
    """No hook file may use bare [zie] log prefix — must be [zie-framework] or [zf]."""
    violations = []
    for hook_py in HOOKS_DIR.glob("*.py"):
        text = hook_py.read_text()
        for lineno, line in enumerate(text.splitlines(), 1):
            if _BARE_ZIE_RE.search(line) and not _VALID_PREFIX_RE.search(line):
                violations.append(f"{hook_py.name}:{lineno}: {line.strip()}")
    assert not violations, (
        "Bare [zie] log prefix found (use [zie-framework] or [zf] instead):\n"
        + "\n".join(violations)
    )
