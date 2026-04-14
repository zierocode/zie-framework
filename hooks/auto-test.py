#!/usr/bin/env python3
"""PostToolUse:Edit/Write hook — run relevant unit tests after file edits.

Features:
- Test→source mapping cache (eliminates duplicate rglob lookups)
- Per-file debounce (not global)
- Cache invalidation on test file change
"""
import hashlib
import json
import os
import re as _re
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

_hook_start = time.monotonic()

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, log_hook_timing, read_event  # noqa: E402
from utils_config import load_config, CACHE_TTLS
from utils_cache import get_cache_manager
from utils_io import project_tmp_path, safe_write_tmp

_SUMMARY_RE = _re.compile(r'\d+\s+(passed|failed|error|skipped|xfailed|xpassed)')
_SKIP_EXTENSIONS = {".md", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".txt"}


class TestLookupCache:
    """Cache test→source file mappings with per-file debounce.

    Usage:
        cache = TestLookupCache(session_id, cwd)
        test_path = cache.get_test_for_source(str(source_path))
        if test_path is None:
            test_path = find_matching_test(...)  # rglob fallback
            cache.set_test_mapping(str(source_path), str(test_path))
        if cache.should_debounce(str(source_path)):
            return  # Skip test run
    """

    def __init__(self, session_id: str, cwd: Path):
        """Initialize test lookup cache.

        Args:
            session_id: Session identifier for isolation
            cwd: Project root directory
        """
        self.session_id = session_id
        self.cwd = cwd
        self.cache = get_cache_manager(cwd)
        self.debounce_ms = CACHE_TTLS.get("test_map", 300) * 1000  # Default 5min for mappings

    def _source_key(self, source_path: str) -> str:
        """Return cache key for source→test mapping."""
        safe_path = _re.sub(r'[^a-zA-Z0-9]', '-', source_path)
        return f"test_source:{safe_path}"

    def _debounce_key(self, source_path: str) -> str:
        """Return cache key for per-file debounce state."""
        safe_path = _re.sub(r'[^a-zA-Z0-9]', '-', source_path)
        return f"test_debounce:{safe_path}"

    def _test_hash_key(self, test_path: str) -> str:
        """Return cache key for test file content hash."""
        safe_path = _re.sub(r'[^a-zA-Z0-9]', '-', test_path)
        return f"test_hash:{safe_path}"

    def get_test_for_source(self, source_path: str) -> Optional[str]:
        """Get cached test path for a source file.

        Returns None on cache miss or if test file no longer exists.
        """
        cached = self.cache.get(self._source_key(source_path), self.session_id)
        if cached:
            test_path = Path(cached)
            if test_path.exists():
                return str(test_path)
            # Test file deleted — invalidate
            self.cache.delete(self._source_key(source_path), self.session_id)
        return None

    def set_test_mapping(self, source_path: str, test_path: str) -> None:
        """Cache test→source mapping with TTL."""
        self.cache.set(
            self._source_key(source_path),
            test_path,
            self.session_id,
            ttl=CACHE_TTLS.get("test_map", 1800),  # 30 min default
        )
        # Also store test file hash for invalidation
        test_file = Path(test_path)
        if test_file.exists():
            try:
                content_hash = hashlib.md5(test_file.read_bytes(), usedforsecurity=False).hexdigest()
                self.cache.set(
                    self._test_hash_key(test_path),
                    {"hash": content_hash, "path": test_path},
                    self.session_id,
                    ttl=CACHE_TTLS.get("test_map", 1800),
                )
            except Exception:
                pass  # Non-fatal

    def invalidate_on_test_change(self, test_path: str) -> bool:
        """Invalidate cache if test file content changed.

        Returns True if invalidated, False if no change or cache miss.
        """
        cached_entry = self.cache.get(self._test_hash_key(test_path), self.session_id)
        if not cached_entry:
            return False

        test_file = Path(test_path)
        if not test_file.exists():
            return False

        try:
            current_hash = hashlib.md5(test_file.read_bytes(), usedforsecurity=False).hexdigest()
            if current_hash != cached_entry.get("hash"):
                # Test file changed — invalidate all source mappings
                # (We don't track reverse mapping, so scan common patterns)
                self.cache.delete(self._test_hash_key(test_path), self.session_id)
                return True
        except Exception:
            pass
        return False

    def should_debounce(self, source_path: str, debounce_ms: int = 5000) -> bool:
        """Check if source file was tested recently (per-file debounce).

        Args:
            source_path: Source file path
            debounce_ms: Debounce window in milliseconds (default: 5000 = 5s)

        Returns:
            True if should skip test run (within debounce window)
        """
        cached = self.cache.get(self._debounce_key(source_path), self.session_id)
        if cached is None:
            return False

        last_tested = cached.get("last_tested", 0)
        age_ms = (time.time() - last_tested) * 1000
        return age_ms < debounce_ms

    def mark_tested(self, source_path: str) -> None:
        """Mark source file as tested (update debounce timestamp)."""
        self.cache.set(
            self._debounce_key(source_path),
            {"last_tested": time.time(), "path": source_path},
            self.session_id,
            ttl=60,  # Short TTL for debounce state
        )


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
    """Find the test file most likely to cover the changed module.

    Note: For cached version, use TestLookupCache.get_test_for_source()
    which wraps this function with caching.
    """
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

    # Initialize test lookup cache (session-scoped)
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    test_cache = TestLookupCache(session_id, cwd)

    # Per-file debounce check (replaces global debounce)
    if test_cache.should_debounce(str(changed)):
        sys.exit(0)  # Within debounce window — skip

    # Test→source mapping cache (eliminates duplicate rglob)
    matching_test = test_cache.get_test_for_source(str(changed))
    if matching_test is None:
        # Cache miss — rglob fallback
        matching_test = find_matching_test(changed, test_runner, cwd)
        if matching_test:
            test_cache.set_test_mapping(str(changed), matching_test)

    # additionalContext injection — only fires when test file exists (after debounce)
    if matching_test:
        print(json.dumps({"additionalContext": f"Affected test: {matching_test}"}))

    auto_test_timeout_ms = config["auto_test_timeout_ms"]
    auto_test_max_wait_s = config["auto_test_max_wait_s"]
    timeout = auto_test_timeout_ms // 1000

    # Build test command
    if test_runner == "pytest":
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
                test_cache.mark_tested(str(changed))
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
                test_cache.mark_tested(str(changed))
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
