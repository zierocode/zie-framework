#!/usr/bin/env python3
"""PostToolUse:Edit/Write hook — run relevant unit tests after file edits."""
import sys
import json
import os
import subprocess
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import project_tmp_path, safe_write_tmp, read_event, get_cwd


def find_matching_test(changed_path: Path, runner: str, cwd: Path) -> str | None:
    """Find the test file most likely to cover the changed module."""
    stem = changed_path.stem  # e.g. "memories" from "memories.py"

    if runner == "pytest":
        tests_dir = cwd / "tests"
        candidates = [
            tests_dir / f"test_{stem}.py",
            tests_dir / f"{stem}_test.py",
        ]
        # Also search recursively
        try:
            for candidate in tests_dir.rglob(f"test_{stem}.py"):
                candidates.append(candidate)
        except OSError:
            pass  # tests/ dir missing or not accessible — candidates stays as-is
        for c in candidates:
            try:
                if c.exists():
                    return str(c)
            except OSError:
                pass

    elif runner in ("vitest", "jest"):
        parent = changed_path.parent
        candidates = [
            parent / f"{stem}.test.ts",
            parent / f"{stem}.test.tsx",
            parent / f"{stem}.spec.ts",
            changed_path.parent.parent / "__tests__" / f"{stem}.test.ts",
        ]
        for c in candidates:
            if c.exists():
                return str(c)

    return None


if __name__ == "__main__":
    event = read_event()

    # Only trigger on Edit/Write
    tool_name = event.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    file_path = (event.get("tool_input") or {}).get("file_path", "")
    if not file_path:
        sys.exit(0)

    cwd = get_cwd()
    zf = cwd / "zie-framework"

    if not zf.exists():
        sys.exit(0)

    # Fast-path: read from session env vars injected by session-resume.py
    test_runner = os.environ.get("ZIE_TEST_RUNNER", "").strip()
    _debounce_env = os.environ.get("ZIE_AUTO_TEST_DEBOUNCE_MS", "").strip()

    # Fallback: read .config when env vars are absent
    config = {}
    if not test_runner or not _debounce_env:
        config_file = zf / ".config"
        if config_file.exists():
            try:
                config = json.loads(config_file.read_text())
            except Exception as e:
                print(
                    f"[zie] warning: .config unreadable ({e}), using defaults",
                    file=sys.stderr,
                )

    if not test_runner:
        test_runner = config.get("test_runner", "")
    if not test_runner:
        sys.exit(0)

    changed = Path(file_path).resolve()
    cwd_resolved = cwd.resolve()
    if not changed.is_relative_to(cwd_resolved):
        sys.exit(0)

    # additionalContext injection — fires before debounce so Claude always gets the hint
    _ctx_test = find_matching_test(changed, test_runner, cwd)
    if _ctx_test:
        _additional_context = f"Affected test: {_ctx_test}"
    else:
        _additional_context = f"No test file found for {changed.name} — write one"
    print(json.dumps({"hookSpecificOutput": {"additionalContext": _additional_context}}))

    # Debounce: skip test run if same file was tested recently (within debounce window)
    if _debounce_env:
        try:
            debounce_ms = int(_debounce_env)
        except (TypeError, ValueError):
            debounce_ms = config.get("auto_test_debounce_ms", 3000)
    else:
        debounce_ms = config.get("auto_test_debounce_ms", 3000)
    debounce_file = project_tmp_path("last-test", cwd.name)
    if debounce_file.exists():
        last_run = debounce_file.stat().st_mtime
        if (time.time() - last_run) < (debounce_ms / 1000):
            sys.exit(0)
    safe_write_tmp(debounce_file, file_path)

    timeout = config.get("auto_test_timeout_ms", 30000) // 1000

    # Build test command
    if test_runner == "pytest":
        matching_test = find_matching_test(changed, "pytest", cwd)
        if matching_test:
            cmd = ["python3", "-m", "pytest", matching_test, "-x", "-q", "--tb=short", "--no-header"]
        else:
            cmd = ["python3", "-m", "pytest", "tests/", "-x", "-q", "--tb=short", "--no-header",
                   "-m", "not integration"]
    elif test_runner == "vitest":
        cmd = ["npx", "vitest", "run", "--reporter=dot"]
    elif test_runner == "jest":
        cmd = ["npx", "jest", "--passWithNoTests", "--no-coverage", "--silent"]
    else:
        sys.exit(0)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            print(f"[zie-framework] Tests pass ✓")
        else:
            print(f"[zie-framework] Tests FAILED — fix before continuing")
            # Print first 20 lines of failure output
            lines = (result.stdout + result.stderr).splitlines()
            for line in lines[:20]:
                if line.strip():
                    print(f"  {line}")
    except subprocess.TimeoutExpired:
        print(f"[zie-framework] Tests timed out ({timeout}s) — check for hanging tests")
    except FileNotFoundError:
        # Test runner not installed — disable quietly
        pass
    except Exception as e:
        print(f"[zie-framework] auto-test: {e}", file=sys.stderr)
