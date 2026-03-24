---
approved: true
approved_at: 2026-03-24
backlog: backlog/configchange-drift-detection.md
spec: specs/2026-03-24-configchange-drift-detection-design.md
---

# ConfigChange CLAUDE.md Drift Detection — Implementation Plan

**Goal:** Add a `config-drift.py` hook that fires on the `ConfigChange` event, classifies the changed file as `CLAUDE.md`, `settings.json`, or `zie-framework/.config`, and injects an `additionalContext` string instructing Claude to re-read the affected file before continuing. Unrecognised paths exit silently.
**Architecture:** New hook `hooks/config-drift.py` + new `ConfigChange` entry in `hooks/hooks.json`. No changes to `utils.py`. Output protocol: JSON `{"additionalContext": "..."}` to stdout (same as `UserPromptSubmit`).
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/config-drift.py` | ConfigChange event handler — classify + emit additionalContext |
| Modify | `hooks/hooks.json` | Add `ConfigChange` top-level event entry |
| Create | `tests/unit/test_hooks_config_drift.py` | Unit tests for all classification branches and guardrails |
| Modify | `zie-framework/project/components.md` | Add `config-drift.py` row to Hooks table |

---

## Task 1: Create `hooks/config-drift.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `CLAUDE.md` path (any depth) → prints `{"additionalContext": "...Re-read it now with Read(...)..."}` and exits 0
- `settings.json` inside a `.claude` directory → prints `additionalContext` about permission rules and exits 0
- `zie-framework/.config` path under `cwd` → prints `additionalContext` about `/zie-resync` and exits 0
- Any other path → prints nothing and exits 0
- Invalid / missing JSON on stdin → prints nothing and exits 0
- `file_path` absent or empty in event → prints nothing and exits 0
- `hook_event_name` not `ConfigChange` → prints nothing and exits 0
- Exit code is always 0 — hook never blocks Claude

**Files:**
- Create: `hooks/config-drift.py`
- Create: `tests/unit/test_hooks_config_drift.py`

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_config_drift.py
"""Tests for hooks/config-drift.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(event: dict, tmp_cwd=None) -> subprocess.CompletedProcess:
    hook = os.path.join(REPO_ROOT, "hooks", "config-drift.py")
    env = {**os.environ}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def run_hook_raw(raw_stdin: str, tmp_cwd=None) -> subprocess.CompletedProcess:
    hook = os.path.join(REPO_ROOT, "hooks", "config-drift.py")
    env = {**os.environ}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    return subprocess.run(
        [sys.executable, hook],
        input=raw_stdin,
        capture_output=True,
        text=True,
        env=env,
    )


def parse_context(r: subprocess.CompletedProcess) -> str:
    """Extract additionalContext string from stdout JSON."""
    return json.loads(r.stdout)["additionalContext"]


# ---------------------------------------------------------------------------
# CLAUDE.md classification
# ---------------------------------------------------------------------------

class TestConfigDriftClaudeMd:
    def test_project_root_claude_md(self, tmp_path):
        path = str(tmp_path / "CLAUDE.md")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        ctx = parse_context(r)
        assert "CLAUDE.md" in ctx
        assert f"Read('{path}')" in ctx

    def test_nested_claude_md(self, tmp_path):
        path = str(tmp_path / ".claude" / "CLAUDE.md")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        ctx = parse_context(r)
        assert "CLAUDE.md" in ctx
        assert f"Read('{path}')" in ctx

    def test_claude_md_context_mentions_instructions(self, tmp_path):
        path = str(tmp_path / "CLAUDE.md")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        ctx = parse_context(r)
        assert "instructions" in ctx.lower()


# ---------------------------------------------------------------------------
# settings.json classification
# ---------------------------------------------------------------------------

class TestConfigDriftSettingsJson:
    def test_claude_settings_json(self, tmp_path):
        path = str(tmp_path / ".claude" / "settings.json")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        ctx = parse_context(r)
        assert "settings.json" in ctx
        assert f"Read('{path}')" in ctx

    def test_settings_json_context_mentions_permission(self, tmp_path):
        path = str(tmp_path / ".claude" / "settings.json")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        ctx = parse_context(r)
        assert "permission" in ctx.lower()

    def test_settings_json_outside_claude_dir_is_silent(self, tmp_path):
        # settings.json NOT inside a .claude directory — should be silent
        path = str(tmp_path / "config" / "settings.json")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# zie-framework/.config classification
# ---------------------------------------------------------------------------

class TestConfigDriftZieConfig:
    def test_zie_framework_config(self, tmp_path):
        path = str(tmp_path / "zie-framework" / ".config")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        ctx = parse_context(r)
        assert "/zie-resync" in ctx

    def test_zie_config_context_mentions_reload(self, tmp_path):
        path = str(tmp_path / "zie-framework" / ".config")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        ctx = parse_context(r)
        # must tell Claude to reload
        assert "reload" in ctx.lower() or "resync" in ctx.lower()

    def test_dot_config_outside_zie_framework_is_silent(self, tmp_path):
        # .config under some other directory — should be silent
        path = str(tmp_path / "other-dir" / ".config")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Unrecognised / unrelated paths
# ---------------------------------------------------------------------------

class TestConfigDriftUnrelated:
    def test_unrelated_json_file_is_silent(self, tmp_path):
        path = str(tmp_path / ".claude" / "custom_commands.json")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_readme_is_silent(self, tmp_path):
        path = str(tmp_path / "README.md")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_arbitrary_py_file_is_silent(self, tmp_path):
        path = str(tmp_path / "hooks" / "auto-test.py")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Outer guard: bad input, wrong event, missing fields
# ---------------------------------------------------------------------------

class TestConfigDriftGuardrails:
    def test_invalid_json_exits_0_silently(self, tmp_path):
        r = run_hook_raw("not valid json", tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_stdin_exits_0_silently(self, tmp_path):
        r = run_hook_raw("", tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_wrong_event_name_is_silent(self, tmp_path):
        path = str(tmp_path / "CLAUDE.md")
        r = run_hook({"hook_event_name": "PreToolUse", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_missing_file_path_key_is_silent(self, tmp_path):
        r = run_hook({"hook_event_name": "ConfigChange"}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_file_path_is_silent(self, tmp_path):
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": ""}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_missing_hook_event_name_is_silent(self, tmp_path):
        path = str(tmp_path / "CLAUDE.md")
        r = run_hook({"file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_exit_code_always_0_on_claude_md(self, tmp_path):
        path = str(tmp_path / "CLAUDE.md")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0

    def test_exit_code_always_0_on_unrelated(self, tmp_path):
        path = str(tmp_path / "random.txt")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
```

Run: `make test-unit` — must FAIL (`hooks/config-drift.py` does not exist; subprocess returns non-zero or empty output where JSON is expected)

### Step 2: Implement (GREEN)

```python
# hooks/config-drift.py
"""ConfigChange hook — detect CLAUDE.md / settings.json / zie-framework/.config drift.

Fires on ConfigChange events. Classifies the changed file and emits
additionalContext JSON instructing Claude to re-read the affected file
before continuing. Unrecognised paths exit silently.

Output protocol: JSON {"additionalContext": "..."} to stdout (same as
UserPromptSubmit hooks). Exit code is always 0 — hook never blocks Claude.
"""
import json
import sys
from pathlib import Path

# Outer guard ----------------------------------------------------------------
try:
    raw = sys.stdin.read()
    event = json.loads(raw)
except Exception:
    sys.exit(0)

try:
    if event.get("hook_event_name") != "ConfigChange":
        sys.exit(0)

    file_path = event.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Resolve path object. Path() raises ValueError on null bytes — caught by
    # the outer guard above if it propagates, but we keep it inside the inner
    # try for clarity.
    try:
        changed = Path(file_path)
    except Exception:
        sys.exit(0)

    # Resolve cwd for the zie-framework/.config branch.
    import os
    cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))

    # -------------------------------------------------------------------------
    # Three-way classification (evaluated in order; first match wins)
    # -------------------------------------------------------------------------

    # Branch A: CLAUDE.md — matches on filename alone (any depth)
    if changed.name == "CLAUDE.md":
        msg = (
            f"[zie-framework] CLAUDE.md has been updated on disk. "
            f"Re-read it now with Read('{file_path}') before continuing "
            f"so your instructions are current."
        )

    # Branch B: settings.json inside a .claude directory
    elif changed.name == "settings.json" and ".claude" in changed.parts:
        msg = (
            f"[zie-framework] .claude/settings.json has been updated on disk. "
            f"Re-read it now with Read('{file_path}') before continuing "
            f"so your permission rules are current."
        )

    # Branch C: .config under cwd/zie-framework/
    elif changed.name == ".config" and changed.is_relative_to(cwd / "zie-framework"):
        msg = (
            "[zie-framework] zie-framework/.config has changed. "
            "Run /zie-resync to reload project configuration before continuing."
        )

    # No match — unrelated config change, stay quiet
    else:
        sys.exit(0)

    # Inner operation: emit additionalContext ---------------------------------
    print(json.dumps({"additionalContext": msg}))
    sys.exit(0)

except Exception as e:
    print(f"[zie-framework] config-drift: {e}", file=sys.stderr)
    sys.exit(0)
```

Run: `make test-unit` — must PASS

### Step 3: Refactor

No structural changes required. Confirm:
- The outer `except Exception` guard wraps only the JSON parse and early-exit block; the inner `except Exception as e` wraps all file-path and classification logic.
- `import os` is inside the inner try — acceptable since it is stdlib and will never fail; if preferred, move to module top (no test impact).
- Docstring accurately describes the three classification branches.
- No `.config` path check omitted (`is_relative_to` requires Python 3.9+; confirm the repo's minimum Python version is 3.9 or replace with `str(changed).startswith(str(cwd / "zie-framework"))` for 3.8 compatibility).

Run: `make test-unit` — still PASS

---

## Task 2: Register `ConfigChange` in `hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks.json` contains a top-level `ConfigChange` key at the same level as `SessionStart`, `UserPromptSubmit`, etc.
- The matcher is `project_settings|user_settings`
- The command points to `config-drift.py` using the `${CLAUDE_PLUGIN_ROOT}` variable
- All other existing hook entries are unchanged
- JSON is valid (parseable by `json.loads`)

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `tests/unit/test_hooks_config_drift.py` (add structural validation test)

### Step 1: Write failing test (RED)

Add the following class to `tests/unit/test_hooks_config_drift.py`:

```python
# tests/unit/test_hooks_config_drift.py — add after TestConfigDriftGuardrails

class TestConfigDriftHooksJsonRegistration:
    def test_configchange_entry_exists(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            data = json.load(f)
        assert "ConfigChange" in data["hooks"], \
            "ConfigChange key missing from hooks.json"

    def test_configchange_has_matcher(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            data = json.load(f)
        entry = data["hooks"]["ConfigChange"]
        assert isinstance(entry, list) and len(entry) > 0
        assert "matcher" in entry[0], "ConfigChange entry missing 'matcher'"
        assert entry[0]["matcher"] == "project_settings|user_settings"

    def test_configchange_command_points_to_config_drift(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            data = json.load(f)
        entry = data["hooks"]["ConfigChange"]
        commands = [h["command"] for h in entry[0]["hooks"] if "command" in h]
        assert any("config-drift.py" in cmd for cmd in commands), \
            "No hook command pointing to config-drift.py found"

    def test_existing_entries_unchanged(self):
        hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
        with open(hooks_path) as f:
            data = json.load(f)
        existing_events = {"SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"}
        for event in existing_events:
            assert event in data["hooks"], f"Existing event {event!r} was removed"
```

Run: `make test-unit` — must FAIL (`ConfigChange` key absent from `hooks.json`)

### Step 2: Implement (GREEN)

Edit `hooks/hooks.json` — add the `ConfigChange` block after the `UserPromptSubmit` entry (before `PostToolUse`). The diff target section is the `"hooks"` object:

```json
  "ConfigChange": [
    {
      "matcher": "project_settings|user_settings",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/config-drift.py\""
        }
      ]
    }
  ],
```

Full resulting `"hooks"` object order after edit:
`SessionStart` → `UserPromptSubmit` → `ConfigChange` → `PostToolUse` → `PreToolUse` → `Stop`

Run: `make test-unit` — must PASS

### Step 3: Refactor

Verify the full `hooks.json` is still valid JSON:

```bash
python3 -c "import json; json.load(open('hooks/hooks.json'))" && echo OK
```

Confirm the `_hook_output_protocol` comment block at the top of `hooks.json` does not need a new entry — `ConfigChange` follows the `UserPromptSubmit` output protocol (JSON `{"additionalContext": "..."}`), and a note can be added to `_hook_output_protocol` for clarity but is not required for correctness.

Run: `make test-unit` — still PASS

---

## Task 3: Update `zie-framework/project/components.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `components.md` Hooks table contains a row for `config-drift.py`
- Row accurately describes the event (`ConfigChange`) and behaviour
- No existing rows are altered

**Files:**
- Modify: `zie-framework/project/components.md`

### Step 1: Write failing test (RED)

Add to `tests/unit/test_hooks_config_drift.py`:

```python
class TestConfigDriftComponentsDoc:
    def test_config_drift_in_components_md(self):
        components_path = os.path.join(
            REPO_ROOT, "zie-framework", "project", "components.md"
        )
        with open(components_path) as f:
            content = f.read()
        assert "config-drift.py" in content, \
            "config-drift.py row missing from components.md Hooks table"

    def test_configchange_event_documented(self):
        components_path = os.path.join(
            REPO_ROOT, "zie-framework", "project", "components.md"
        )
        with open(components_path) as f:
            content = f.read()
        assert "ConfigChange" in content, \
            "ConfigChange event not documented in components.md"
```

Run: `make test-unit` — must FAIL

### Step 2: Implement (GREEN)

Append the following row to the Hooks table in `zie-framework/project/components.md` (after the `utils.py` row):

```
| config-drift.py | ConfigChange:project_settings\|user_settings | ตรวจ CLAUDE.md / settings.json / zie-framework/.config drift → inject additionalContext to re-read |
```

Also update the `**Last updated:**` date to `2026-03-24`.

Run: `make test-unit` — must PASS

### Step 3: Refactor

No structural changes needed. Confirm the table still renders correctly (pipes aligned, no broken rows).

Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/config-drift.py hooks/hooks.json tests/unit/test_hooks_config_drift.py zie-framework/project/components.md && git commit -m "feat: ConfigChange drift detection for CLAUDE.md, settings.json, zie-framework/.config"`*
