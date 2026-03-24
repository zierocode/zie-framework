---
approved: true
approved_at: 2026-03-24
backlog: backlog/pretooluse-input-modification.md
spec: specs/2026-03-24-pretooluse-input-modification-design.md
---

# PreToolUse updatedInput Path Sanitization + Rewriting — Implementation Plan

**Goal:** Create `hooks/input-sanitizer.py` — a new `PreToolUse` hook that silently fixes relative `file_path` arguments in `Write`/`Edit` calls and wraps risky-but-legitimate `Bash` commands in an interactive confirmation prompt. Both rewrites emit `updatedInput` + `permissionDecision: "allow"` so Claude never stalls on a re-prompt.
**Architecture:** Standalone new hook registered alongside `safety-check.py` in `hooks/hooks.json`. Reads event via existing `read_event()` / `get_cwd()` from `utils.py` — no changes to `utils.py` required. Two execution paths: (1) Write|Edit — relative-path resolution with boundary check, (2) Bash — `CONFIRM_PATTERNS` match and command rewrite.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/input-sanitizer.py` | New PreToolUse hook — path resolution + Bash rewrite |
| Modify | `hooks/hooks.json` | Register `input-sanitizer.py` as second PreToolUse hook |
| Create | `tests/unit/test_input_sanitizer.py` | Full unit test suite |

---

## Task 1: Create `hooks/input-sanitizer.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- For `Write` or `Edit` with a relative `file_path`: outputs `{"updatedInput": {..., "file_path": "<abs>"}, "permissionDecision": "allow"}` to stdout, exits 0.
- For `Write` or `Edit` with an absolute `file_path`: no stdout output, exits 0.
- For `Write` or `Edit` with a traversal path that escapes `cwd`: no stdout output, warning to stderr, exits 0.
- For `Bash` matching a `CONFIRM_PATTERNS` entry: outputs `{"updatedInput": {"command": "<wrapped>"}, "permissionDecision": "allow"}` to stdout, exits 0.
- For `Bash` not matching any pattern: no stdout output, exits 0.
- For any other tool name (`Read`, etc.): no stdout output, exits 0.
- Invalid JSON on stdin: exits 0 (handled by `read_event()`).
- Hook never exits non-zero. Hook never crashes.

**Files:**
- Create: `hooks/input-sanitizer.py`
- Create: `tests/unit/test_input_sanitizer.py`

### Step 1 — RED: Write failing tests

```python
# tests/unit/test_input_sanitizer.py

"""Tests for hooks/input-sanitizer.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "input-sanitizer.py")


def run_hook(tool_name, tool_input, cwd_override=None):
    """Run input-sanitizer.py with the given event, optionally overriding CLAUDE_CWD."""
    event = {"tool_name": tool_name, "tool_input": tool_input}
    env = os.environ.copy()
    if cwd_override:
        env["CLAUDE_CWD"] = cwd_override
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# Write / Edit — relative path resolution
# ---------------------------------------------------------------------------

class TestWriteRelativePath:
    def test_relative_path_resolved_to_absolute(self, tmp_path):
        r = run_hook("Write", {"file_path": "src/main.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["permissionDecision"] == "allow"
        assert out["updatedInput"]["file_path"] == str(tmp_path / "src" / "main.py")

    def test_absolute_path_produces_no_output(self, tmp_path):
        abs_path = str(tmp_path / "src" / "main.py")
        r = run_hook("Write", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_traversal_path_produces_no_output(self, tmp_path):
        r = run_hook("Write", {"file_path": "../../etc/passwd"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_traversal_path_logs_stderr_warning(self, tmp_path):
        r = run_hook("Write", {"file_path": "../../etc/passwd"}, cwd_override=str(tmp_path))
        assert "input-sanitizer" in r.stderr

    def test_missing_file_path_key_exits_cleanly(self):
        r = run_hook("Write", {"content": "hello"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_file_path_exits_cleanly(self):
        r = run_hook("Write", {"file_path": ""})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_other_tool_input_fields_preserved(self, tmp_path):
        r = run_hook(
            "Write",
            {"file_path": "out.txt", "content": "hello world"},
            cwd_override=str(tmp_path),
        )
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["updatedInput"]["content"] == "hello world"

    def test_idempotent_on_already_absolute(self, tmp_path):
        abs_path = str(tmp_path / "already_absolute.py")
        r = run_hook("Write", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestEditRelativePath:
    def test_edit_relative_path_resolved(self, tmp_path):
        r = run_hook("Edit", {"file_path": "hooks/utils.py"}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["updatedInput"]["file_path"] == str(tmp_path / "hooks" / "utils.py")

    def test_edit_absolute_path_unchanged(self, tmp_path):
        abs_path = str(tmp_path / "hooks" / "utils.py")
        r = run_hook("Edit", {"file_path": abs_path}, cwd_override=str(tmp_path))
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Bash — CONFIRM_PATTERNS rewrite
# ---------------------------------------------------------------------------

class TestBashConfirmRewrite:
    def test_rm_rf_dotslash_path_rewritten(self):
        r = run_hook("Bash", {"command": "rm -rf ./dist/"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert out["permissionDecision"] == "allow"
        cmd = out["updatedInput"]["command"]
        assert "Would run:" in cmd
        assert "read -p" in cmd
        assert "rm -rf ./dist/" in cmd

    def test_rm_f_dotslash_rewritten(self):
        r = run_hook("Bash", {"command": "rm -f ./build/output.o"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_git_clean_fd_rewritten(self):
        r = run_hook("Bash", {"command": "git clean -fd"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_make_clean_rewritten(self):
        r = run_hook("Bash", {"command": "make clean"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_truncate_size_zero_rewritten(self):
        r = run_hook("Bash", {"command": "truncate --size 0 logfile.txt"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]

    def test_safe_command_produces_no_output(self):
        r = run_hook("Bash", {"command": "echo hello"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_git_status_produces_no_output(self):
        r = run_hook("Bash", {"command": "git status"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_double_wrapping_on_reentrant_call(self):
        """Command already containing confirmation wrapper must not be re-wrapped."""
        already_wrapped = (
            'echo "Would run: rm -rf ./dist/" && read -p "Confirm? [y/N] " _y '
            '&& [ "$_y" = "y" ] && { rm -rf ./dist/; }'
        )
        r = run_hook("Bash", {"command": already_wrapped})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_missing_command_key_exits_cleanly(self):
        r = run_hook("Bash", {"other_key": "value"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_command_exits_cleanly(self):
        r = run_hook("Bash", {"command": ""})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_only_first_pattern_matched_on_multi_match(self):
        """When a command matches multiple CONFIRM_PATTERNS, only one rewrite is applied."""
        r = run_hook("Bash", {"command": "rm -rf ./a/ && make clean"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        # Wrapped exactly once — the wrapping phrase appears exactly once
        assert out["updatedInput"]["command"].count("Would run:") == 1

    def test_whitespace_normalization_matches(self):
        r = run_hook("Bash", {"command": "rm  -rf  ./dist/"})
        assert r.returncode == 0
        out = json.loads(r.stdout)
        assert "Would run:" in out["updatedInput"]["command"]


# ---------------------------------------------------------------------------
# Non-targeted tools
# ---------------------------------------------------------------------------

class TestNonTargetedTools:
    def test_read_tool_produces_no_output(self):
        r = run_hook("Read", {"file_path": "some/file.py"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_glob_tool_produces_no_output(self):
        r = run_hook("Glob", {"pattern": "**/*.py"})
        assert r.returncode == 0
        assert r.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Error resilience
# ---------------------------------------------------------------------------

class TestErrorResilience:
    def test_invalid_json_stdin_exits_zero(self):
        r = subprocess.run(
            [sys.executable, HOOK],
            input="not json at all",
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0

    def test_none_tool_input_exits_zero(self):
        event = {"tool_name": "Write", "tool_input": None}
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps(event),
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""
```

Run: `make test-unit` — must **FAIL** (`hooks/input-sanitizer.py` does not exist yet; import will fail).

---

### Step 2 — GREEN: Implement `hooks/input-sanitizer.py`

```python
# hooks/input-sanitizer.py

#!/usr/bin/env python3
"""PreToolUse hook — resolve relative file_path args and wrap risky Bash commands."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import get_cwd, read_event

# Bash commands that are legitimate but warrant interactive confirmation.
# MUST NOT overlap with safety-check.py BLOCKS — those are hard stops.
CONFIRM_PATTERNS = [
    r"rm\s+-rf\s+\./",        # rm -rf ./<path>  (project-relative recursive delete)
    r"rm\s+-f\s+\./",         # rm -f ./<path>   (project-relative force delete)
    r"git\s+clean\s+-fd",     # git clean -fd    (removes untracked files)
    r"make\s+clean",          # make clean       (may delete build artifacts)
    r"truncate\s+--size\s+0", # truncate --size 0 (zeroing a file)
]

# ── Outer guard ──────────────────────────────────────────────────────────────
try:
    event = read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}

    if tool_name not in {"Write", "Edit", "Bash"}:
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Write / Edit — relative path resolution ──────────────────────────────────
if tool_name in {"Write", "Edit"}:
    try:
        file_path = tool_input.get("file_path", "")
        if not file_path:
            sys.exit(0)

        p = Path(file_path)
        if p.is_absolute():
            sys.exit(0)

        cwd = get_cwd().resolve()
        abs_path = (cwd / p).resolve()

        # Boundary check — must stay inside project root
        if not str(abs_path).startswith(str(cwd)):
            print(
                f"[zie-framework] input-sanitizer: relative path escapes cwd, skipping rewrite: {file_path}",
                file=sys.stderr,
            )
            sys.exit(0)

        updated = dict(tool_input)
        updated["file_path"] = str(abs_path)
        print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
        sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] input-sanitizer: {e}", file=sys.stderr)
        sys.exit(0)

# ── Bash — confirm-before-run rewrite ────────────────────────────────────────
if tool_name == "Bash":
    try:
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        # Preserve original case (unlike safety-check which lowercases)
        normalized = re.sub(r"\s+", " ", command.strip())

        for pattern in CONFIRM_PATTERNS:
            if re.search(pattern, normalized):
                rewritten = (
                    f'echo "Would run: {command}" '
                    f'&& read -p "Confirm? [y/N] " _y '
                    f'&& [ "$_y" = "y" ] && {{ {command}; }}'
                )
                updated = dict(tool_input)
                updated["command"] = rewritten
                print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
                sys.exit(0)
    except Exception as e:
        print(f"[zie-framework] input-sanitizer: {e}", file=sys.stderr)
        sys.exit(0)
```

Run: `make test-unit` — must **PASS**.

---

### Step 3 — REFACTOR

Review checklist (no behavioral changes):

- Confirm `CONFIRM_PATTERNS` entries carry inline comments explaining each pattern.
- Confirm the boundary check uses `str(abs_path).startswith(str(cwd))` — acceptable for POSIX paths; note in a comment that this is a prefix check and both sides are `.resolve()`-ed (symlinks followed).
- Confirm the Bash path preserves original command casing (not lowercased like `safety-check.py`).
- Confirm the module-level docstring accurately describes both paths.

No structural changes expected. Run: `make test-unit` — still **PASS**.

---

## Task 2: Register `PreToolUse:Bash` hook in `hooks/hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `hooks/hooks.json` has a second `PreToolUse` entry (or the existing entry is expanded) that runs `input-sanitizer.py` for `Write`, `Edit`, and `Bash` tools.
- `safety-check.py` remains the first hook in execution order (it may exit 2 and abort; `input-sanitizer.py` only runs when `safety-check.py` exits 0).
- The registration uses `${CLAUDE_PLUGIN_ROOT}` path convention, matching all other entries.
- All existing tests continue to pass.

**Files:**
- Modify: `hooks/hooks.json`

### Step 1 — RED: Write failing test

```python
# tests/unit/test_input_sanitizer.py — add new class at the bottom

class TestHooksJsonRegistration:
    def test_input_sanitizer_registered_in_hooks_json(self):
        hooks_path = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})
        pre_tool_hooks = hooks.get("PreToolUse", [])
        # Collect all command strings from all PreToolUse hook entries
        all_commands = []
        for entry in pre_tool_hooks:
            for h in entry.get("hooks", []):
                all_commands.append(h.get("command", ""))
        assert any("input-sanitizer.py" in cmd for cmd in all_commands), (
            "input-sanitizer.py must be registered in hooks.json PreToolUse"
        )

    def test_safety_check_still_registered(self):
        hooks_path = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_path.read_text())
        hooks = data.get("hooks", {})
        pre_tool_hooks = hooks.get("PreToolUse", [])
        all_commands = []
        for entry in pre_tool_hooks:
            for h in entry.get("hooks", []):
                all_commands.append(h.get("command", ""))
        assert any("safety-check.py" in cmd for cmd in all_commands), (
            "safety-check.py must remain registered in hooks.json PreToolUse"
        )
```

Run: `make test-unit` — must **FAIL** (`input-sanitizer.py` not yet in `hooks.json`).

---

### Step 2 — GREEN: Update `hooks/hooks.json`

Current `PreToolUse` block (matcher: `"Bash"`, one hook):

```json
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
]
```

Replace with two separate entries — `safety-check.py` first (Bash only), then `input-sanitizer.py` covering all three tools:

```json
"PreToolUse": [
  {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety-check.py\""
      }
    ]
  },
  {
    "matcher": "Write|Edit|Bash",
    "hooks": [
      {
        "type": "command",
        "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/input-sanitizer.py\""
      }
    ]
  }
]
```

Execution order guarantee: Claude Code fires hooks in array order per matcher. For a `Bash` call, `safety-check.py` fires first. If it exits 2, `input-sanitizer.py` is never reached. If it exits 0, `input-sanitizer.py` runs and may emit `updatedInput`. For `Write`/`Edit` calls, only `input-sanitizer.py` fires (no `safety-check.py` entry matches those tools).

Run: `make test-unit` — must **PASS**.

---

### Step 3 — REFACTOR

- Confirm the `_hook_output_protocol` comment block at the top of `hooks.json` reflects the `updatedInput` + `permissionDecision` output format for `PreToolUse` rewrites. Update if needed:

  ```json
  "_hook_output_protocol": {
    ...
    "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block; OR {\"updatedInput\": {...}, \"permissionDecision\": \"allow\"} to rewrite input",
    ...
  }
  ```

- Confirm JSON is valid (no trailing commas, balanced braces).

Run: `make test-unit` — still **PASS**.

---

## Output Protocol Reference

When a rewrite is needed, `input-sanitizer.py` prints exactly this JSON to stdout (one line, no trailing newline required):

```json
{"updatedInput": {"file_path": "/absolute/resolved/path.py", "content": "..."}, "permissionDecision": "allow"}
```

For Bash rewrites:

```json
{"updatedInput": {"command": "echo \"Would run: rm -rf ./dist/\" && read -p \"Confirm? [y/N] \" _y && [ \"$_y\" = \"y\" ] && { rm -rf ./dist/; }"}, "permissionDecision": "allow"}
```

When no rewrite is needed: **no stdout output at all**, exit 0.
When an error occurs: message to stderr only, exit 0 — Claude is never blocked.

---

## Commit

```
git add hooks/input-sanitizer.py hooks/hooks.json tests/unit/test_input_sanitizer.py && git commit -m "feat: PreToolUse input-sanitizer — relative path resolution and Bash confirm-rewrite"
```
