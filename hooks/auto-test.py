#!/usr/bin/env python3
"""PostToolUse:Edit/Write hook — run relevant unit tests after file edits."""
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

_hook_start = time.monotonic()

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, load_config, log_hook_timing, project_tmp_path, read_event, safe_write_tmp  # noqa: E402


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
                print("[zie-framework] Tests FAILED — fix before continuing")
                lines = (stdout_data + stderr_data).splitlines()
                for line in lines[:20]:
                    if line.strip():
                        print(f"  {line}")
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
                print("[zie-framework] Tests FAILED — fix before continuing")
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

    log_hook_timing(
        "auto-test",
        int((time.monotonic() - _hook_start) * 1000),
        0,
        session_id=os.environ.get("CLAUDE_SESSION_ID", ""),
    )
