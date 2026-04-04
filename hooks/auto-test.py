#!/usr/bin/env python3
"""PostToolUse:Edit/Write hook — run relevant unit tests after file edits."""
import json
import os
import re as _re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

_hook_start = time.monotonic()

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, log_hook_timing, read_event  # noqa: E402
from utils_config import load_config
from utils_io import project_tmp_path, safe_write_tmp

_SUMMARY_RE = _re.compile(r'\d+\s+(passed|failed|error|skipped|xfailed|xpassed)')
_SKIP_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt"}


def truncate_test_output(raw: str) -> str:
    """Reduce pytest output to summary line + first FAILED block, capped at 30 lines."""
    lines = raw.splitlines()

    # Find summary line (last matching line)
    summary_line = ""
    for line in reversed(lines):
        if _SUMMARY_RE.search(line):
            summary_line = line.strip()
            break

    # Find first FAILED block
    failed_block: list[str] = []
    in_block = False
    for line in lines:
        if not in_block and _re.match(r'^(FAILED|E   |_ )', line):
            in_block = True
        if in_block:
            if not line.strip() or line.startswith('='):
                break
            failed_block.append(line)

    header = "[zie-framework] Tests FAILED — fix before continuing"

    if failed_block:
        parts = [header]
        if summary_line:
            parts.append(summary_line)
        parts.append("")
        parts.extend(failed_block)
        result = "\n".join(parts)
        result_lines = result.splitlines()
        if len(result_lines) > 30:
            result = "\n".join(result_lines[:30])
        return result
    else:
        non_empty = [ln for ln in lines if ln.strip()][:10]
        parts = [header]
        if summary_line:
            parts.append(summary_line)
        parts.append("")
        parts.extend(non_empty)
        return "\n".join(parts)


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

    # Always load config for validated defaults (env vars override specific keys below)
    config = load_config(cwd)

    if not test_runner:
        test_runner = config.get("test_runner")
    if not test_runner:
        sys.exit(0)

    changed = Path(file_path).resolve()

    # Skip non-code files silently — no tests, no debounce write
    if changed.suffix.lower() in _SKIP_EXTENSIONS:
        sys.exit(0)

    cwd_resolved = cwd.resolve()
    if not changed.is_relative_to(cwd_resolved):
        sys.exit(0)

    # additionalContext injection — fires before debounce so Claude always gets the hint
    _ctx_test = find_matching_test(changed, test_runner, cwd)
    if _ctx_test:
        _additional_context = f"Affected test: {_ctx_test}"
    else:
        _additional_context = f"No test file found for {changed.name} — write one"
    print(json.dumps({"additionalContext": _additional_context}))

    # Debounce: skip test run if same file was tested recently (within debounce window)
    if _debounce_env:
        try:
            debounce_ms = int(_debounce_env)
        except (TypeError, ValueError):
            debounce_ms = config.get("auto_test_debounce_ms")
    else:
        debounce_ms = config.get("auto_test_debounce_ms")
    debounce_file = project_tmp_path("last-test", cwd.name)
    if debounce_ms > 0 and debounce_file.exists():
        last_run = debounce_file.stat().st_mtime
        if (time.time() - last_run) < (debounce_ms / 1000):
            sys.exit(0)
    safe_write_tmp(debounce_file, file_path)

    auto_test_timeout_ms = config["auto_test_timeout_ms"]
    auto_test_max_wait_s = config["auto_test_max_wait_s"]
    timeout = auto_test_timeout_ms // 1000

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
        if auto_test_max_wait_s > 0:
            # Wall-clock guard path: Popen + threading.Timer
            timed_out = threading.Event()

            def _kill_on_timeout(proc):
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except OSError:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                timed_out.set()
                print(
                    f"[zie-framework] auto-test: timed out after {auto_test_max_wait_s}s"
                    f" — tests may be hanging. Run make test-unit manually."
                )

            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            timer = threading.Timer(auto_test_max_wait_s, _kill_on_timeout, args=[proc])
            try:
                timer.start()
                stdout_data, stderr_data = proc.communicate()
                rc = proc.returncode
            finally:
                timer.cancel()

            if timed_out.is_set():
                sys.exit(0)

            if rc == 0:
                print("[zie-framework] Tests pass ✓")
            else:
                print(truncate_test_output(stdout_data + stderr_data))
        else:
            # Fallback path: subprocess.run with auto_test_timeout_ms
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if result.returncode == 0:
                print("[zie-framework] Tests pass ✓")
            else:
                print(truncate_test_output(result.stdout + result.stderr))
    except subprocess.TimeoutExpired:
        print(f"[zie-framework] Tests timed out ({timeout}s) — check for hanging tests")
    except FileNotFoundError:
        # Test runner not installed — disable quietly
        pass
    except Exception as e:
        print(f"[zie-framework] auto-test: {e}", file=sys.stderr)

    log_hook_timing(
        "auto-test",
        int((time.monotonic() - _hook_start) * 1000),
        0,
        session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
    )
