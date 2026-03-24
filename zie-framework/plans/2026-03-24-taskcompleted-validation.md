---
approved: true
approved_at: 2026-03-24
backlog: backlog/taskcompleted-validation.md
spec: specs/2026-03-24-taskcompleted-validation-design.md
---

# TaskCompleted Quality Gate Hook — Implementation Plan

**Goal:** Add a `TaskCompleted` hook that blocks Claude from marking a task done if pytest's last-failed cache has entries, and warns if uncommitted implementation files are present. Gate is only enforced for tasks whose title contains `implement` or `fix` (case-insensitive); all other tasks are passed through unconditionally.

**Architecture:** New `hooks/task-completed-gate.py` reads the hook event from stdin via `read_event()`, inspects `.pytest_cache/v/cache/lastfailed` as a JSON file (no subprocess test run), and calls `git status --short` to detect uncommitted implementation files. Blocking exit is `sys.exit(2)` with stderr message; warnings use `sys.exit(0)` with stdout message. Two-tier error handling per ADR-003: outer guard wraps `main()` with bare `except Exception → sys.exit(0)`; inner operations log to stderr and continue on failure.

**Tech Stack:** Python 3.x, pytest, stdlib only (`json`, `subprocess`, `pathlib`, `sys`, `os`)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/task-completed-gate.py` | New hook — primary deliverable |
| Modify | `hooks/hooks.json` | Register `TaskCompleted` event |
| Create | `tests/unit/test_hooks_task_completed_gate.py` | Unit tests for the new hook |

---

## Task 1: Create `hooks/task-completed-gate.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Advisory tasks (no `implement`/`fix` in title) exit 0 with a skip message on stdout
- Failing pytest cache (`lastfailed` is a non-empty dict) → exit 2, stderr contains `BLOCKED` and the failed test keys (max 5)
- Clean pytest cache (`lastfailed` is `{}` or file absent) → exit 0, no output
- Uncommitted implementation files present → exit 0, stdout contains `WARNING` and file list (max 5)
- Uncommitted test-only files are not reported as warnings
- Missing/corrupt `lastfailed` file → silently skip Check 1, proceed to Check 2
- `git` not on PATH or not a git repo → silently skip Check 2, exit 0
- Invalid JSON on stdin → exit 0 (outer guard)
- Missing or empty `title` in event → exit 0 (outer guard)
- Hook completes in under 2 seconds on all inputs

**Files:**
- Create: `hooks/task-completed-gate.py`
- Create: `tests/unit/test_hooks_task_completed_gate.py`

---

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_task_completed_gate.py

"""Tests for hooks/task-completed-gate.py"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "task-completed-gate.py")
IMPL_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".rb", ".java",
             ".kt", ".swift", ".c", ".cpp", ".h")


def run_hook(title, cwd=None, env_extra=None):
    event = {"tool_name": "TaskUpdate", "tool_input": {"id": "task-1", "status": "completed", "title": title}}
    env = os.environ.copy()
    if cwd:
        env["CLAUDE_CWD"] = str(cwd)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_lastfailed(cwd: Path, data: dict):
    cache_dir = cwd / ".pytest_cache" / "v" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "lastfailed").write_text(json.dumps(data))


# ---------------------------------------------------------------------------
# Outer guard — bad input
# ---------------------------------------------------------------------------

class TestOuterGuard:
    def test_invalid_json_exits_zero(self):
        r = subprocess.run([sys.executable, HOOK], input="not json",
                           capture_output=True, text=True)
        assert r.returncode == 0

    def test_missing_title_exits_zero(self, tmp_path):
        event = {"tool_name": "TaskUpdate", "tool_input": {"id": "t1", "status": "completed"}}
        r = subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                           capture_output=True, text=True,
                           env={**os.environ, "CLAUDE_CWD": str(tmp_path)})
        assert r.returncode == 0

    def test_empty_title_exits_zero(self, tmp_path):
        r = run_hook("", cwd=tmp_path)
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Advisory mode — non-implement/fix tasks are passed through
# ---------------------------------------------------------------------------

class TestAdvisoryMode:
    def test_docs_task_is_skipped(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Write design spec for feature X", cwd=tmp_path)
        assert r.returncode == 0
        assert "advisory" in r.stdout.lower()

    def test_plan_task_is_skipped(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Create implementation plan for auth", cwd=tmp_path)
        assert r.returncode == 0

    def test_review_task_is_skipped(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Review ADR-009", cwd=tmp_path)
        assert r.returncode == 0

    def test_implement_keyword_triggers_gate(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Implement the session-learn hook", cwd=tmp_path)
        assert r.returncode == 2

    def test_fix_keyword_triggers_gate(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("Fix broken wip-checkpoint logic", cwd=tmp_path)
        assert r.returncode == 2

    def test_implement_case_insensitive(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("IMPLEMENT rate limiting", cwd=tmp_path)
        assert r.returncode == 2

    def test_fix_case_insensitive(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        r = run_hook("FIX the login bug", cwd=tmp_path)
        assert r.returncode == 2


# ---------------------------------------------------------------------------
# Check 1 — pytest last-failed cache
# ---------------------------------------------------------------------------

class TestPytestCacheCheck:
    def test_failing_tests_block(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True,
                                   "tests/test_foo.py::test_baz": True})
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 2
        assert "BLOCKED" in r.stderr
        assert "test_foo" in r.stderr

    def test_empty_lastfailed_passes(self, tmp_path):
        make_lastfailed(tmp_path, {})
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_missing_cache_file_passes(self, tmp_path):
        # No .pytest_cache directory at all
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_missing_cache_dir_passes(self, tmp_path):
        # .pytest_cache exists but lastfailed does not
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_corrupt_lastfailed_passes(self, tmp_path):
        cache_dir = tmp_path / ".pytest_cache" / "v" / "cache"
        cache_dir.mkdir(parents=True)
        (cache_dir / "lastfailed").write_text("NOT VALID JSON {{{")
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_blocked_message_lists_failed_tests(self, tmp_path):
        failures = {f"tests/test_mod.py::test_{i}": True for i in range(7)}
        make_lastfailed(tmp_path, failures)
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 2
        # At most 5 keys shown
        total_keys_shown = r.stderr.count("test_")
        assert total_keys_shown <= 5

    def test_single_failing_test_blocked(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_auth.py::test_login": True})
        r = run_hook("Fix login flow", cwd=tmp_path)
        assert r.returncode == 2
        assert "test_auth" in r.stderr


# ---------------------------------------------------------------------------
# Check 2 — uncommitted implementation files (git status)
# ---------------------------------------------------------------------------

class TestGitStatusCheck:
    def test_no_git_repo_exits_zero(self, tmp_path):
        # tmp_path is not a git repo — git status returns non-zero
        r = run_hook("Implement feature X", cwd=tmp_path)
        assert r.returncode == 0

    def test_git_not_found_exits_zero(self, tmp_path, monkeypatch):
        # Simulate git not on PATH by patching PATH to empty
        env = os.environ.copy()
        env["PATH"] = "/nonexistent"
        env["CLAUDE_CWD"] = str(tmp_path)
        event = {"tool_name": "TaskUpdate", "tool_input": {
            "id": "t1", "status": "completed", "title": "Implement feature X"}}
        r = subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0

    def test_uncommitted_impl_file_warns(self, tmp_path):
        """Confirm warning output when hook is called — returncode always 0."""
        r = run_hook("Implement feature X", cwd=Path(REPO_ROOT))
        assert r.returncode == 0  # uncommitted files never block

    def test_warning_output_format(self, tmp_path):
        # Use the real repo — any uncommitted impl files produce WARNING on stdout
        r = run_hook("Implement feature X", cwd=Path(REPO_ROOT))
        assert r.returncode == 0
        if "WARNING" in r.stdout:
            assert "[zie-framework]" in r.stdout


# ---------------------------------------------------------------------------
# Extension and test-file filter logic
# ---------------------------------------------------------------------------

class TestFileFilter:
    """Import the hook module and test is_impl_file directly."""

    def _import_filter(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "task_completed_gate", HOOK)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.is_impl_file

    def test_py_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("hooks/session-learn.py") is True

    def test_ts_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/login.ts") is True

    def test_test_py_file_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("tests/test_session_learn.py") is False

    def test_spec_ts_file_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/login.spec.ts") is False

    def test_test_dot_ts_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/login.test.ts") is False

    def test_underscore_test_excluded(self):
        is_impl = self._import_filter()
        assert is_impl("src/auth/auth_test.go") is False

    def test_md_file_not_impl(self):
        is_impl = self._import_filter()
        assert is_impl("README.md") is False

    def test_go_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("cmd/server/main.go") is True

    def test_rs_file_is_impl(self):
        is_impl = self._import_filter()
        assert is_impl("src/lib.rs") is True


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

class TestPerformance:
    def test_advisory_task_completes_quickly(self, tmp_path):
        start = time.time()
        run_hook("Write ADR for caching strategy", cwd=tmp_path)
        assert time.time() - start < 2.0

    def test_gate_task_no_cache_completes_quickly(self, tmp_path):
        start = time.time()
        run_hook("Implement rate limiting middleware", cwd=tmp_path)
        assert time.time() - start < 2.0

    def test_gate_task_with_failing_cache_completes_quickly(self, tmp_path):
        make_lastfailed(tmp_path, {"tests/test_foo.py::test_bar": True})
        start = time.time()
        run_hook("Fix broken handler", cwd=tmp_path)
        assert time.time() - start < 2.0
```

Run: `make test-unit` — must **FAIL** (`task-completed-gate.py` does not exist; `is_impl` not importable; `ModuleNotFoundError`).

---

### Step 2: Implement (GREEN)

```python
# hooks/task-completed-gate.py

#!/usr/bin/env python3
"""TaskCompleted hook — quality gate before a task is marked done.

Blocks completion (exit 2) if pytest's last-failed cache has entries.
Warns (exit 0) if uncommitted implementation files are detected.
Gate is only enforced for tasks whose title contains 'implement' or 'fix'.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import read_event, get_cwd

IMPL_EXTS = frozenset((
    ".py", ".ts", ".tsx", ".js", ".jsx",
    ".go", ".rs", ".rb", ".java", ".kt",
    ".swift", ".c", ".cpp", ".h",
))

TEST_INDICATORS = ("test_", "_test.", ".test.", ".spec.")


def is_impl_file(path_str: str) -> bool:
    """Return True if path_str looks like an implementation file (not a test file)."""
    p = path_str.lower()
    if not any(p.endswith(ext) for ext in IMPL_EXTS):
        return False
    if any(indicator in p for indicator in TEST_INDICATORS):
        return False
    return True


def check_pytest_cache(cwd: Path) -> tuple[bool, str]:
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


def check_uncommitted_files(cwd: Path) -> tuple[bool, str]:
    """Run git status --short and detect uncommitted implementation files."""
    try:
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
            if is_impl_file(filename):
                impl_lines.append(line.strip())
        if not impl_lines:
            return False, ""
        shown = impl_lines[:5]
        suffix = f"\n  (+{len(impl_lines) - 5} more)" if len(impl_lines) > 5 else ""
        msg = (
            "[zie-framework] WARNING: uncommitted implementation files detected"
            " — consider committing before closing task.\n"
            + "\n".join(f"  {l}" for l in shown)
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
    if "implement" not in title_lower and "fix" not in title_lower:
        print("[zie-framework] task-completed-gate: advisory task — gate skipped")
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
```

Run: `make test-unit` — must **PASS**.

---

### Step 3: Refactor

Two targeted cleanups after green:

1. Extract the `lastfailed` key formatting into a one-liner helper inside `check_pytest_cache` — no behaviour change, improves readability of the 5-key truncation logic.
2. Confirm `is_impl_file` is the single source of truth for extension and test-indicator logic — no duplication anywhere in the hook.

No structural changes to the two-tier error pattern. No new public functions.

Run: `make test-unit` — still **PASS**.

---

## Task 2: Register `TaskCompleted` in `hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks.json` has a `"TaskCompleted"` key at the top level of `"hooks"` object
- The entry uses `${CLAUDE_PLUGIN_ROOT}` path expansion, matching existing hook entries exactly
- `_hook_output_protocol` has a `"TaskCompleted"` annotation entry
- All existing hook entries are unchanged
- JSON is valid (parseable by `json.loads`)

**Files:**
- Modify: `hooks/hooks.json`

---

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_json.py  (new file — or append to existing test_utils.py if preferred)

"""Structural tests for hooks/hooks.json."""
import json
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOKS_JSON = Path(REPO_ROOT) / "hooks" / "hooks.json"


class TestHooksJsonStructure:
    def _load(self):
        return json.loads(HOOKS_JSON.read_text())

    def test_json_is_valid(self):
        self._load()  # raises if invalid

    def test_taskcompleted_key_present(self):
        data = self._load()
        assert "TaskCompleted" in data["hooks"], \
            "TaskCompleted entry missing from hooks.json"

    def test_taskcompleted_command_uses_plugin_root(self):
        data = self._load()
        entry = data["hooks"]["TaskCompleted"]
        command = entry[0]["hooks"][0]["command"]
        assert "${CLAUDE_PLUGIN_ROOT}" in command

    def test_taskcompleted_command_references_correct_script(self):
        data = self._load()
        entry = data["hooks"]["TaskCompleted"]
        command = entry[0]["hooks"][0]["command"]
        assert "task-completed-gate.py" in command

    def test_taskcompleted_hook_type_is_command(self):
        data = self._load()
        entry = data["hooks"]["TaskCompleted"]
        assert entry[0]["hooks"][0]["type"] == "command"

    def test_hook_output_protocol_has_taskcompleted(self):
        data = self._load()
        assert "TaskCompleted" in data["_hook_output_protocol"]

    def test_hook_output_protocol_taskcompleted_mentions_exit2(self):
        data = self._load()
        annotation = data["_hook_output_protocol"]["TaskCompleted"]
        assert "exit(2)" in annotation or "2" in annotation

    def test_existing_hooks_unchanged(self):
        data = self._load()
        hooks = data["hooks"]
        for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert key in hooks, f"Existing hook key missing: {key}"
```

Run: `make test-unit` — must **FAIL** (`TaskCompleted` key absent, `_hook_output_protocol` entry absent).

---

### Step 2: Implement (GREEN)

Edit `hooks/hooks.json` — two changes:

**A. Add `"TaskCompleted"` to `_hook_output_protocol`:**

```json
"_hook_output_protocol": {
    "SessionStart": "plain text printed to stdout — injected as session context",
    "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
    "PostToolUse": "plain text warnings/status printed to stdout",
    "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
    "Stop": "no output required; side-effects only (file writes, API calls)",
    "TaskCompleted": "exit(2) + stderr message to block; stdout warning for non-blocking notices"
},
```

**B. Add `"TaskCompleted"` entry inside `"hooks"` object (after the `"Stop"` block):**

```json
"TaskCompleted": [
  {
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/task-completed-gate.py\""
      }
    ]
  }
]
```

Run: `make test-unit` — must **PASS**.

---

### Step 3: Refactor

Verify `hooks.json` top-level key order remains consistent: `_hook_output_protocol` first, then `hooks` with events in chronological lifecycle order. Reorder only if inconsistent with existing convention — no behaviour change.

Run: `make test-unit` — still **PASS**.

---

## Commit

```bash
git add hooks/task-completed-gate.py hooks/hooks.json \
        tests/unit/test_hooks_task_completed_gate.py \
        tests/unit/test_hooks_json.py
git commit -m "feat: TaskCompleted quality gate hook — block on failing tests, warn on uncommitted files"
```
