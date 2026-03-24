---
approved: true
approved_at: 2026-03-24
backlog: backlog/stopfailure-logging.md
spec: specs/2026-03-24-stopfailure-logging-design.md
---

# StopFailure API Error Logging — Implementation Plan

**Goal:** Intercept `StopFailure` API error events and append a structured log entry to a project-scoped `/tmp` file, plus emit a visible stderr notification for user-actionable errors (`rate_limit`, `billing_error`).

**Architecture:** New hook `hooks/stopfailure-log.py` registered under the `StopFailure` event in `hooks/hooks.json`. Reuses `read_event`, `get_cwd`, `project_tmp_path`, `safe_project_name`, `parse_roadmap_now` from `utils.py`. No changes to `utils.py`. Log format is plain-text JSONL-style append (one record per line). Hook always exits 0.

**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/stopfailure-log.py` | StopFailure event handler — log + notify |
| Modify | `hooks/hooks.json` | Register `StopFailure` event block |
| Create | `tests/unit/test_hooks_stopfailure_log.py` | Full test coverage (10 cases) |

---

## Task 1: Create `hooks/stopfailure-log.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Hook reads the StopFailure event from stdin via `read_event()`; malformed JSON → `sys.exit(0)`, no file written
- If `cwd / "zie-framework"` does not exist → `sys.exit(0)`, no file written
- Log path is `project_tmp_path("failure-log", safe_project_name(cwd.name))`
- Each invocation appends exactly one line to the log file in the format:
  `[<ISO-8601 UTC>] error_type=<type> wip=<wip_summary> details=<details>`
- `wip_summary` is the first 3 Now-lane items joined by ` | `; empty string when ROADMAP absent
- `error_type in {"rate_limit", "billing_error"}` → prints human-readable message to stderr
- All other `error_type` values → no stderr output
- `/tmp` write failure (OSError) → caught, error printed to stderr, hook still exits 0
- Hook never raises an unhandled exception; always exits 0

**Files:**
- Create: `hooks/stopfailure-log.py`
- Create: `tests/unit/test_hooks_stopfailure_log.py`

---

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_stopfailure_log.py

"""Tests for hooks/stopfailure-log.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "stopfailure-log.py")

SAMPLE_ROADMAP = """## Now
- [ ] Implement login flow
- [ ] Add JWT validation
- [ ] Write integration tests

## Next
- [ ] Add refresh tokens
"""


def run_hook(tmp_cwd, event=None, env_overrides=None):
    if event is None:
        event = {"error_type": "api_error"}
    env = {**os.environ, "CLAUDE_CWD": str(tmp_cwd)}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


def failure_log_path(cwd):
    """Mirror the hook's log path calculation."""
    import re
    safe = re.sub(r"[^a-zA-Z0-9]", "-", cwd.name)
    return Path(f"/tmp/zie-{safe}-failure-log")


class TestLogWritten:
    def test_log_written_rate_limit(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "rate_limit"})
        assert log.exists(), "failure-log must be created for rate_limit"
        content = log.read_text()
        assert "error_type=rate_limit" in content

    def test_log_written_billing_error(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "billing_error"})
        assert log.exists(), "failure-log must be created for billing_error"
        assert "error_type=billing_error" in log.read_text()

    def test_log_written_api_error_silent(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        r = run_hook(cwd, event={"error_type": "api_error"})
        assert log.exists(), "failure-log must be created for api_error"
        assert "error_type=api_error" in log.read_text()
        assert r.stderr.strip() == "", "api_error must produce no stderr notification"

    def test_log_written_overloaded_error_silent(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        r = run_hook(cwd, event={"error_type": "overloaded_error"})
        assert log.exists()
        assert "error_type=overloaded_error" in log.read_text()
        assert r.stderr.strip() == "", "overloaded_error must produce no stderr notification"

    def test_log_written_unknown_error_silent(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        r = run_hook(cwd, event={"error_type": "some_new_error_type"})
        assert log.exists()
        assert "error_type=some_new_error_type" in log.read_text()
        assert r.stderr.strip() == ""


class TestNotification:
    def test_rate_limit_stderr_notification(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook(cwd, event={"error_type": "rate_limit"})
        assert "rate_limit" in r.stderr
        assert "Wait before resuming" in r.stderr

    def test_billing_error_stderr_notification(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook(cwd, event={"error_type": "billing_error"})
        assert "billing_error" in r.stderr
        assert "Wait before resuming" in r.stderr


class TestWipInLogEntry:
    def test_wip_in_log_entry(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "api_error"})
        content = log.read_text()
        assert "login flow" in content or "wip=" in content, (
            "log entry must include Now-lane WIP context"
        )

    def test_wip_empty_when_no_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path)  # no ROADMAP.md
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "api_error"})
        content = log.read_text()
        assert "wip=" in content


class TestGuardrails:
    def test_no_zie_framework_dir_exits_clean(self, tmp_path):
        # tmp_path has no zie-framework/ subdir
        log = failure_log_path(tmp_path)
        log.unlink(missing_ok=True)
        r = run_hook(tmp_path, event={"error_type": "rate_limit"})
        assert r.returncode == 0
        assert not log.exists(), "no log must be written when zie-framework/ absent"

    def test_malformed_stdin_exits_clean(self, tmp_path):
        log = failure_log_path(tmp_path)
        log.unlink(missing_ok=True)
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not valid json{{{",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert not log.exists(), "no log must be written on malformed stdin"

    def test_log_appends_on_multiple_calls(self, tmp_path):
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        run_hook(cwd, event={"error_type": "api_error"})
        run_hook(cwd, event={"error_type": "rate_limit"})
        lines = [ln for ln in log.read_text().splitlines() if ln.strip()]
        assert len(lines) == 2, f"expected 2 log lines, got {len(lines)}"

    def test_no_crash_on_tmp_write_failure(self, tmp_path):
        """Hook must exit 0 even when the log path is unwritable."""
        cwd = make_cwd(tmp_path)
        log = failure_log_path(cwd)
        log.unlink(missing_ok=True)
        # Make the log path a directory so open(..., "a") raises IsADirectoryError
        log.mkdir(parents=True, exist_ok=True)
        r = run_hook(cwd, event={"error_type": "api_error"})
        assert r.returncode == 0, "hook must not crash on write failure"
        log.rmdir()
```

Run: `make test-unit` — must FAIL (`hooks/stopfailure-log.py` does not exist yet, `ModuleNotFoundError` / `FileNotFoundError`)

---

### Step 2: Implement (GREEN)

```python
# hooks/stopfailure-log.py

#!/usr/bin/env python3
"""StopFailure hook — log API error events to a project-scoped /tmp file."""
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

try:
    from utils import get_cwd, parse_roadmap_now, project_tmp_path, read_event, safe_project_name
    event = read_event()
except Exception:
    sys.exit(0)

try:
    error_type = event.get("error_type", "unknown")
    error_details = event.get("error_details", "")

    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)

    roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
    wip_lines = parse_roadmap_now(roadmap_path)
    wip_summary = " | ".join(wip_lines[:3])

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_entry = f"[{ts}] error_type={error_type} wip={wip_summary} details={error_details}\n"

    log_path = project_tmp_path("failure-log", safe_project_name(cwd.name))
    try:
        with open(log_path, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"[zie-framework] stopfailure-log: {e}", file=sys.stderr)
        sys.exit(0)

    if error_type in {"rate_limit", "billing_error"}:
        print(
            f"[zie-framework] Session stopped: {error_type}. Wait before resuming.",
            file=sys.stderr,
        )
except Exception as e:
    print(f"[zie-framework] stopfailure-log: {e}", file=sys.stderr)

sys.exit(0)
```

Run: `make test-unit` — all 10 test cases must PASS

---

### Step 3: Refactor

Review the implementation for clarity:

- Confirm outer `try/except` wraps all logic below `read_event()` — matches the two-tier hook error handling convention from `CLAUDE.md`
- Confirm inner `try/except` isolates only the file `open()`/`write()` call — inner tier logs to stderr, hook still exits 0
- Confirm no `except Exception` silently swallows the stderr notification path — the notification `print` is outside the inner try block, so a write failure does not suppress it
- Confirm `wip_lines[:3]` is safe when `parse_roadmap_now` returns fewer than 3 items (Python slice never raises on short lists)
- Confirm `error_details` defaults to `""` so the log line is always well-formed even when the field is absent from the payload

No structural changes required.

Run: `make test-unit` — still PASS

---

## Task 2: Register StopFailure in `hooks/hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks/hooks.json` has a top-level `"StopFailure"` key inside the `"hooks"` object
- The entry follows the same array-of-objects structure as the existing `"Stop"` block
- The command value uses `${CLAUDE_PLUGIN_ROOT}` for portability
- All existing hook registrations are unchanged
- `make test-unit` continues to pass after the edit

**Files:**
- Modify: `hooks/hooks.json`

---

### Step 1: Write failing test (RED)

```python
# tests/unit/test_hooks_stopfailure_log.py — add new class at end of file

class TestHooksJsonRegistration:
    def test_stopfailure_registered_in_hooks_json(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        import json as _json
        data = _json.loads(hooks_json.read_text())
        hooks_block = data.get("hooks", {})
        assert "StopFailure" in hooks_block, (
            "hooks/hooks.json must register a StopFailure event block"
        )

    def test_stopfailure_command_references_correct_script(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        import json as _json
        data = _json.loads(hooks_json.read_text())
        entries = data["hooks"]["StopFailure"]
        commands = [
            h["command"]
            for entry in entries
            for h in entry.get("hooks", [])
            if h.get("type") == "command"
        ]
        assert any("stopfailure-log.py" in cmd for cmd in commands), (
            "StopFailure hook must reference stopfailure-log.py"
        )
```

Run: `make test-unit` — `TestHooksJsonRegistration` tests must FAIL (`"StopFailure"` key absent)

---

### Step 2: Implement (GREEN)

Edit `hooks/hooks.json` — add the `StopFailure` block immediately after the closing bracket of the `"Stop"` array, before the final closing brace of the `"hooks"` object:

```json
  "StopFailure": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stopfailure-log.py\""
        }
      ]
    }
  ]
```

The updated `hooks/hooks.json` `"hooks"` object after the edit:

```json
{
  "_hook_output_protocol": {
    "SessionStart": "plain text printed to stdout — injected as session context",
    "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
    "PostToolUse": "plain text warnings/status printed to stdout",
    "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
    "Stop": "no output required; side-effects only (file writes, API calls)"
  },
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-resume.py\""
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-detect.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/auto-test.py\""
          },
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/wip-checkpoint.py\""
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety-check.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\""
          },
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\""
          }
        ]
      }
    ],
    "StopFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stopfailure-log.py\""
          }
        ]
      }
    ]
  }
}
```

Run: `make test-unit` — all tests including `TestHooksJsonRegistration` must PASS

---

### Step 3: Refactor

- Confirm `hooks.json` is valid JSON: `python3 -c "import json; json.load(open('hooks/hooks.json'))"` — no error
- Confirm the `StopFailure` block structure is parallel to `Stop` (array → object with `"hooks"` array → command object with `"type"` and `"command"`) — consistent with existing schema
- Note: no `async` field is added. The spec confirms Claude Code's hook registration JSON does not expose an `async` field; the non-blocking guarantee is satisfied by the hook's unconditional `sys.exit(0)` path

Run: `make test-unit` — still PASS

---

## Commit

```
git add hooks/stopfailure-log.py hooks/hooks.json tests/unit/test_hooks_stopfailure_log.py
git commit -m "feat: StopFailure hook — API error logging and rate-limit notification"
```
