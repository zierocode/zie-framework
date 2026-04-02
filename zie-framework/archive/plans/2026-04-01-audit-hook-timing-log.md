---
slug: audit-hook-timing-log
status: approved
approved: true
date: 2026-04-01
---

# Plan: Structured Hook Timing Log

## Overview

Add a `log_hook_timing(hook_name, duration_ms, exit_code, session_id)` helper
to `hooks/utils.py`. Instrument 4 key hooks to call it at exit. Timing entries
are JSON lines appended to the existing session-scoped notification log under
`/tmp/zie-<project>/timing.log`. Zero cost when `session_id` is absent.

**Spec:** `zie-framework/specs/2026-04-01-audit-hook-timing-log-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `log_hook_timing` writes a JSON line `{hook, duration_ms, exit_code, ts}` to the session timing log |
| AC-2 | `log_hook_timing` is a no-op when `session_id` is empty or None |
| AC-3 | `log_hook_timing` never raises — all errors silently ignored |
| AC-4 | `session-resume.py` calls `log_hook_timing` at exit |
| AC-5 | `auto-test.py` calls `log_hook_timing` at exit |
| AC-6 | Unit tests for AC-1, AC-2, AC-3 all pass; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Write failing tests (RED)

**File:** `tests/unit/test_utils.py`

Add `TestLogHookTiming` class:

```python
import json
from pathlib import Path
from hooks.utils import log_hook_timing


class TestLogHookTiming:
    def test_writes_json_line_to_timing_log(self, tmp_path, monkeypatch):
        """AC-1."""
        import tempfile
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        log_hook_timing("session-resume", 42, 0, session_id="test-proj")
        log_path = tmp_path / "zie-test-proj" / "timing.log"
        assert log_path.exists()
        entry = json.loads(log_path.read_text().strip())
        assert entry["hook"] == "session-resume"
        assert entry["duration_ms"] == 42
        assert entry["exit_code"] == 0
        assert "ts" in entry

    def test_noop_when_session_id_empty(self, tmp_path, monkeypatch):
        """AC-2."""
        monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
        log_hook_timing("session-resume", 10, 0, session_id="")
        log_hook_timing("session-resume", 10, 0, session_id=None)
        # No files should be created
        assert not any(tmp_path.rglob("timing.log"))

    def test_never_raises_on_bad_path(self, tmp_path, monkeypatch):
        """AC-3."""
        # Point gettempdir to a non-writable path
        monkeypatch.setattr("tempfile.gettempdir", lambda: "/nonexistent_root_dir_xyz")
        # Must not raise
        log_hook_timing("session-resume", 10, 0, session_id="test")
```

Run `make test-unit` — RED confirmed (3 failures).

---

### Task 2 — Add helper to utils.py (partial GREEN)

**File:** `hooks/utils.py`

**Add after existing imports (append near end of helpers section):**

```python
def log_hook_timing(
    hook_name: str,
    duration_ms: int,
    exit_code: int,
    session_id: str | None = None,
) -> None:
    """Append a JSON timing entry to the session timing log.

    No-op when session_id is empty or None. Never raises.
    """
    if not session_id:
        return
    try:
        import json as _json
        from datetime import datetime, timezone
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        log_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
        log_dir.mkdir(parents=True, exist_ok=True)
        entry = _json.dumps({
            "hook": hook_name,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "ts": datetime.now(timezone.utc).isoformat(),
        })
        with open(log_dir / "timing.log", "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass
```

Run `make test-unit` — TestLogHookTiming GREEN.

---

### Task 3 — Instrument key hooks

**File:** `hooks/session-resume.py`

At the end of the file, before (or replacing) `sys.exit(0)`:

```python
# Timing log (best-effort)
import time as _time
_hook_end = _time.monotonic()
try:
    from utils import log_hook_timing
    log_hook_timing(
        "session-resume",
        int((_hook_end - _hook_start) * 1000),
        0,
        session_id=getattr(_config, 'get', lambda *a: None)('session_id') or
                   os.environ.get("CLAUDE_SESSION_ID", ""),
    )
except Exception:
    pass
```

And add at the top (after imports):
```python
import time as _time
_hook_start = _time.monotonic()
```

**File:** `hooks/auto-test.py` — same `_hook_start` + `log_hook_timing` pattern at exit.

---

### Task 4 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

| Layer | Test | AC |
|-------|------|----|
| Unit | test_writes_json_line_to_timing_log | AC-1 |
| Unit | test_noop_when_session_id_empty | AC-2 |
| Unit | test_never_raises_on_bad_path | AC-3 |
| Manual | Check /tmp/zie-*/timing.log after session | AC-4, AC-5 |

---

## Rollout

1. Write failing tests (Task 1) — RED.
2. Add `log_hook_timing` to utils.py (Task 2) — partial GREEN.
3. Instrument session-resume.py and auto-test.py (Task 3).
4. Run `make test-ci` (Task 4) — full suite gate.
5. Mark ROADMAP Done.
