---
slug: audit-stopfailure-stderr
status: approved
approved: true
date: 2026-04-01
---

# Plan: Surface All Non-Trivial StopFailure Error Types to stderr

## Overview

Expand the stderr output in `hooks/stopfailure-log.py` from 2 error types
(`rate_limit`, `billing_error`) to 4 (`+ context_limit`, `api_error`). Add a
tailored hint for `context_limit` ("Use /compact or start a new session.").

**Spec:** `zie-framework/specs/2026-04-01-audit-stopfailure-stderr-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `context_limit` → prints "[zie-framework] Session stopped: context_limit. Use /compact or start a new session." to stderr |
| AC-2 | `api_error` → prints "[zie-framework] Session stopped: api_error." to stderr |
| AC-3 | `rate_limit` / `billing_error` still print existing "Wait before resuming." message |
| AC-4 | `unknown` error type does NOT print to stderr (not actionable) |
| AC-5 | All 4 unit tests pass; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Write failing tests (RED)

**File:** `tests/unit/test_stopfailure_log.py`

Add `TestStderrMessages` class:

```python
import importlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_utils_stub(cwd: Path, wip_lines=None):
    """Return a minimal utils stub for stopfailure-log tests."""
    stub = types.ModuleType("utils")
    stub.get_cwd = lambda: cwd
    stub.parse_roadmap_now = lambda p: wip_lines or []
    stub.project_tmp_path = lambda *a: cwd / "failure-log.tmp"
    stub.safe_project_name = lambda n: n
    stub.sanitize_log_field = lambda s: s
    stub.read_event = lambda: json.loads(sys.stdin.readline())
    return stub


class TestStderrMessages:
    def _run(self, tmp_path, error_type, capsys, monkeypatch):
        """Load stopfailure-log with patched utils; return captured stderr."""
        stub = _make_utils_stub(tmp_path)
        (tmp_path / "zie-framework").mkdir()
        monkeypatch.setitem(sys.modules, "utils", stub)
        event_json = json.dumps({"error_type": error_type, "error_details": ""})
        monkeypatch.setattr("sys.stdin", __import__("io").StringIO(event_json + "\n"))
        import hooks.stopfailure_log as m  # adjust import path as needed
        # re-import to pick up patched utils
        if "hooks.stopfailure_log" in sys.modules:
            del sys.modules["hooks.stopfailure_log"]
        captured = capsys.readouterr()
        return captured.err

    def test_context_limit_prints_to_stderr(self, tmp_path, capsys, monkeypatch):
        """AC-1."""
        stub = _make_utils_stub(tmp_path)
        (tmp_path / "zie-framework").mkdir()
        stub.read_event = lambda: {"error_type": "context_limit", "error_details": ""}
        monkeypatch.setitem(sys.modules, "utils", stub)
        with patch("builtins.open", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: None, write=lambda x: None)):
            import importlib, sys as _sys
            spec = importlib.util.spec_from_file_location(
                "stopfailure_log", Path("hooks/stopfailure-log.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        out = capsys.readouterr().err
        assert "context_limit" in out
        assert "/compact" in out

    def test_api_error_prints_to_stderr(self, tmp_path, capsys, monkeypatch):
        """AC-2."""
        stub = _make_utils_stub(tmp_path)
        (tmp_path / "zie-framework").mkdir()
        stub.read_event = lambda: {"error_type": "api_error", "error_details": ""}
        monkeypatch.setitem(sys.modules, "utils", stub)
        with patch("builtins.open", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: None, write=lambda x: None)):
            import importlib
            spec = importlib.util.spec_from_file_location(
                "stopfailure_log2", Path("hooks/stopfailure-log.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        out = capsys.readouterr().err
        assert "api_error" in out

    def test_rate_limit_still_works(self, tmp_path, capsys, monkeypatch):
        """AC-3."""
        stub = _make_utils_stub(tmp_path)
        (tmp_path / "zie-framework").mkdir()
        stub.read_event = lambda: {"error_type": "rate_limit", "error_details": ""}
        monkeypatch.setitem(sys.modules, "utils", stub)
        with patch("builtins.open", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: None, write=lambda x: None)):
            import importlib
            spec = importlib.util.spec_from_file_location(
                "stopfailure_log3", Path("hooks/stopfailure-log.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        out = capsys.readouterr().err
        assert "rate_limit" in out
        assert "Wait before resuming" in out

    def test_unknown_silent(self, tmp_path, capsys, monkeypatch):
        """AC-4: unknown error type should NOT emit a user-facing message."""
        stub = _make_utils_stub(tmp_path)
        (tmp_path / "zie-framework").mkdir()
        stub.read_event = lambda: {"error_type": "unknown", "error_details": ""}
        monkeypatch.setitem(sys.modules, "utils", stub)
        with patch("builtins.open", return_value=MagicMock(__enter__=lambda s: s, __exit__=lambda *a: None, write=lambda x: None)):
            import importlib
            spec = importlib.util.spec_from_file_location(
                "stopfailure_log4", Path("hooks/stopfailure-log.py")
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        out = capsys.readouterr().err
        assert "Session stopped" not in out
```

Run `make test-unit` — RED confirmed (4 failures).

---

### Task 2 — Implement (GREEN)

**File:** `hooks/stopfailure-log.py`

**Before (lines 38–43):**
```python
    if error_type in {"rate_limit", "billing_error"}:
        print(
            f"[zie-framework] Session stopped: {error_type}. Wait before resuming.",
            file=sys.stderr,
        )
```

**After:**
```python
    _STOP_MESSAGES = {
        "rate_limit": "Wait before resuming.",
        "billing_error": "Wait before resuming.",
        "context_limit": "Use /compact or start a new session.",
        "api_error": "",
    }
    if error_type in _STOP_MESSAGES:
        hint = _STOP_MESSAGES[error_type]
        suffix = f" {hint}" if hint else ""
        print(f"[zie-framework] Session stopped: {error_type}.{suffix}", file=sys.stderr)
```

Run `make test-unit` — GREEN.

---

### Task 3 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

| Layer | Test | AC |
|-------|------|----|
| Unit | test_context_limit_prints_to_stderr | AC-1 |
| Unit | test_api_error_prints_to_stderr | AC-2 |
| Unit | test_rate_limit_still_works | AC-3 |
| Unit | test_unknown_silent | AC-4 |

---

## Rollout

1. Write failing tests (Task 1) — RED.
2. Apply str_replace to stopfailure-log.py (Task 2) — GREEN.
3. Run `make test-ci` (Task 3) — no regression.
4. Mark ROADMAP Done.
