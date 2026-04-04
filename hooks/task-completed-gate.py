#!/usr/bin/env python3
"""TaskCompleted hook — quality gate before a task is marked done.

Blocks completion (exit 2) if pytest's last-failed cache has entries.
Warns (exit 0) if uncommitted implementation files are detected.
Gate is only enforced for tasks whose title contains 'implement' or 'fix'.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_config import load_config

IMPL_EXTS = frozenset((
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".h",
))

_DEFAULT_TEST_INDICATORS = ("test_", "_test.", ".test.", ".spec.")


def _load_test_indicators(cwd: Path) -> tuple:
    """Load TEST_INDICATORS from .config or fall back to hardcoded defaults.

    Config key: test_indicators (comma-separated, e.g. "test_, _test., .test.")
    Falls back to default tuple when key is absent or empty.

    NOTE: load_config() parses JSON. Comma-split on a string value works correctly.
    """
    config = load_config(cwd)
    raw = config.get("test_indicators")
    if raw:
        return tuple(s.strip() for s in raw.split(",") if s.strip())
    return _DEFAULT_TEST_INDICATORS


def is_impl_file(path_str: str, TEST_INDICATORS: tuple = _DEFAULT_TEST_INDICATORS) -> bool:
    """Return True if path_str looks like an implementation file (not a test file)."""
    p = path_str.lower()
    if not any(p.endswith(ext) for ext in IMPL_EXTS):
        return False
    if any(indicator in p for indicator in TEST_INDICATORS):
        return False
    return True


def check_pytest_cache(cwd: Path) -> tuple:
    """Check .pytest_cache/v/cache/lastfailed for failing tests."""
    lastfailed_path = cwd / ".pytest_cache" / "v" / "cache" / "lastfailed"
    try:
        if not lastfailed_path.exists():
            return False, ""
        data = json.loads(lastfailed_path.read_text())
        if not isinstance(data, dict) or not data:
            return False, ""
        keys = list(data.keys())
        shown = keys[:5]
        suffix = f" (+{len(keys) - 5} more)" if len(keys) > 5 else ""
        msg = (
            "[zie-framework] BLOCKED: tests are failing — fix failures before marking done.\n"
            f"Failed: {', '.join(shown)}{suffix}"
        )
        return True, msg
    except (OSError, json.JSONDecodeError):
        return False, ""


def check_uncommitted_files(cwd: Path) -> tuple:
    """Run git status --short and detect uncommitted implementation files."""
    try:
        TEST_INDICATORS = _load_test_indicators(cwd)
        result = subprocess.run(
            ["git", "-C", str(cwd), "status", "--short"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = result.stdout.splitlines()
        impl_lines = []
        for line in lines:
            if len(line) < 3:
                continue
            filename = line[3:].strip()
            if " -> " in filename:
                filename = filename.split(" -> ")[-1].strip()
            if is_impl_file(filename, TEST_INDICATORS):
                impl_lines.append(line.strip())
        if not impl_lines:
            return False, ""
        shown = impl_lines[:5]
        suffix = f"\n  (+{len(impl_lines) - 5} more)" if len(impl_lines) > 5 else ""
        msg = (
            "[zie-framework] WARNING: uncommitted implementation files detected"
            " — consider committing before closing task.\n"
            + "\n".join(f"  {ln}" for ln in shown)
            + suffix
        )
        return True, msg
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False, ""


def main():
    event = read_event()

    title = (event.get("tool_input") or {}).get("title") or ""
    if not title:
        sys.exit(0)

    title_lower = title.lower()
    if not re.search(r'\bimplement\b', title_lower) and not re.search(r'\bfix\b', title_lower):
        sys.exit(0)

    cwd = get_cwd()

    # Check 1 — pytest last-failed cache
    try:
        blocked, block_msg = check_pytest_cache(cwd)
        if blocked:
            print(block_msg, file=sys.stderr)
            sys.exit(2)
    except Exception as e:
        print(f"[zie-framework] task-completed-gate: check_pytest_cache error: {e}",
              file=sys.stderr)

    # Check 2 — uncommitted implementation files
    try:
        warned, warn_msg = check_uncommitted_files(cwd)
        if warned:
            print(warn_msg)
    except Exception as e:
        print(f"[zie-framework] task-completed-gate: check_uncommitted_files error: {e}",
              file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
