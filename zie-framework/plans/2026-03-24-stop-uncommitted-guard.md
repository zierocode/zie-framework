---
approved: true
approved_at: 2026-03-24
backlog: backlog/stop-uncommitted-guard.md
spec: specs/2026-03-24-stop-uncommitted-guard-design.md
---

# Stop Hook Uncommitted Work Guard — Implementation Plan

**Goal:** Create `hooks/stop-guard.py` — a Stop hook that detects uncommitted implementation files and blocks Claude with a concrete commit prompt, preventing work from being silently lost when a session ends or compacts.
**Architecture:** New `hooks/stop-guard.py` runs on every `Stop` event. It checks `event["stop_hook_active"]` first (infinite-loop guard), then runs `git status --short` and filters paths against canonical implementation patterns using `fnmatch`. If matches are found, it emits `{"decision": "block", "reason": "..."}` to stdout and exits 0. Registered as the first hook in the `Stop` list so it runs before `session-learn.py` and `session-cleanup.py`.
**Tech Stack:** Python 3.x, pytest, stdlib only (`subprocess`, `fnmatch`, `json`)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/stop-guard.py` | New Stop hook — uncommitted work detection and block |
| Modify | `hooks/hooks.json` | Prepend `stop-guard.py` as first Stop hook entry |
| Create | `tests/unit/test_stop_guard.py` | Unit test module for stop-guard |
| Modify | `zie-framework/project/components.md` | Add `stop-guard.py` row to Hooks table |

---

## Task 1: Create `hooks/stop-guard.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- Exits 0 immediately when `event["stop_hook_active"]` is truthy — no git call made
- Exits 0 immediately on any stdin parse failure
- Exits 0 when `git status` returns clean (no implementation file paths in output)
- Emits `{"decision": "block", "reason": "..."}` to stdout when uncommitted implementation files are detected
- The reason string lists each matching file path and includes the commit command `git add -A && git commit -m 'feat: <describe change>'`
- Exits 0 on all git errors (not a repo, binary missing, timeout, bare/detached HEAD)
- Matches all six pattern categories: `hooks/*.py`, `tests/*.py`, `commands/*.md`, `skills/**/*.md`, `templates/**/*`, and untracked (`??`) files in those paths
- Never raises an unhandled exception; never exits with a non-zero code

**Files:**
- Create: `hooks/stop-guard.py`
- Create: `tests/unit/test_stop_guard.py`

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_stop_guard.py

"""Tests for hooks/stop-guard.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "stop-guard.py")


def run_hook(event: dict, cwd: str = "/tmp", env_overrides: dict = None):
    env = {**os.environ, "CLAUDE_CWD": cwd}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


# ---------------------------------------------------------------------------
# Infinite-loop guard
# ---------------------------------------------------------------------------

class TestStopHookActiveGuard:
    def test_exits_zero_when_stop_hook_active_true(self, tmp_path):
        """Must exit 0 immediately when stop_hook_active is truthy."""
        r = run_hook({"stop_hook_active": True}, cwd=str(tmp_path))
        assert r.returncode == 0

    def test_no_output_when_stop_hook_active(self, tmp_path):
        """No stdout when stop_hook_active guard fires."""
        r = run_hook({"stop_hook_active": True}, cwd=str(tmp_path))
        assert r.stdout.strip() == ""

    def test_exits_zero_when_stop_hook_active_is_1(self, tmp_path):
        """Integer 1 is also truthy — must be guarded."""
        r = run_hook({"stop_hook_active": 1}, cwd=str(tmp_path))
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Outer guard — bad stdin
# ---------------------------------------------------------------------------

class TestOuterGuard:
    def test_exits_zero_on_empty_stdin(self, tmp_path):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input="",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0

    def test_exits_zero_on_invalid_json(self, tmp_path):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input="{not valid json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Clean git tree — no block
# ---------------------------------------------------------------------------

class TestCleanTree:
    def test_no_block_on_clean_tree(self, tmp_path):
        """A git repo with no uncommitted implementation files must not block."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"],
                       cwd=str(tmp_path), check=True, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t",
                            "GIT_AUTHOR_EMAIL": "t@t.com",
                            "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t.com"})
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "block" not in r.stdout

    def test_no_block_on_docs_only_changes(self, tmp_path):
        """Changes only to ROADMAP.md must not trigger a block."""
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"],
                       cwd=str(tmp_path), check=True, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t",
                            "GIT_AUTHOR_EMAIL": "t@t.com",
                            "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t.com"})
        (tmp_path / "ROADMAP.md").write_text("## Now\n- [ ] thing\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "block" not in r.stdout


# ---------------------------------------------------------------------------
# Block on uncommitted implementation files
# ---------------------------------------------------------------------------

class TestBlockOnUncommittedFiles:
    def _init_repo(self, tmp_path):
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "init"],
                       cwd=str(tmp_path), check=True, capture_output=True,
                       env={**os.environ, "GIT_AUTHOR_NAME": "t",
                            "GIT_AUTHOR_EMAIL": "t@t.com",
                            "GIT_COMMITTER_NAME": "t",
                            "GIT_COMMITTER_EMAIL": "t@t.com"})

    def test_block_on_unstaged_hook_py(self, tmp_path):
        self._init_repo(tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        hook_file = hooks_dir / "my-hook.py"
        hook_file.write_text("# new hook\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        output = json.loads(r.stdout)
        assert output["decision"] == "block"
        assert "hooks/my-hook.py" in output["reason"]

    def test_block_on_unstaged_test_py(self, tmp_path):
        self._init_repo(tmp_path)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_feature.py"
        test_file.write_text("def test_x(): pass\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        output = json.loads(r.stdout)
        assert output["decision"] == "block"
        assert "tests/test_feature.py" in output["reason"]

    def test_block_on_unstaged_command_md(self, tmp_path):
        self._init_repo(tmp_path)
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        cmd_file = commands_dir / "zie-feature.md"
        cmd_file.write_text("# command\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        output = json.loads(r.stdout)
        assert output["decision"] == "block"
        assert "commands/zie-feature.md" in output["reason"]

    def test_block_on_unstaged_skill_md(self, tmp_path):
        self._init_repo(tmp_path)
        skill_dir = tmp_path / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# skill\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        output = json.loads(r.stdout)
        assert output["decision"] == "block"

    def test_block_on_unstaged_template_file(self, tmp_path):
        self._init_repo(tmp_path)
        tmpl_dir = tmp_path / "templates" / "project"
        tmpl_dir.mkdir(parents=True)
        tmpl_file = tmpl_dir / "ROADMAP.md"
        tmpl_file.write_text("## Now\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        output = json.loads(r.stdout)
        assert output["decision"] == "block"

    def test_block_reason_contains_commit_command(self, tmp_path):
        self._init_repo(tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "stop-guard.py").write_text("# new\n")
        r = run_hook({}, cwd=str(tmp_path))
        output = json.loads(r.stdout)
        assert "git add -A && git commit" in output["reason"]

    def test_block_lists_multiple_files(self, tmp_path):
        self._init_repo(tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        (hooks_dir / "hook-a.py").write_text("# a\n")
        (hooks_dir / "hook-b.py").write_text("# b\n")
        r = run_hook({}, cwd=str(tmp_path))
        output = json.loads(r.stdout)
        assert "hook-a.py" in output["reason"]
        assert "hook-b.py" in output["reason"]

    def test_staged_file_also_triggers_block(self, tmp_path):
        """Staged but not yet committed files must also trigger a block."""
        self._init_repo(tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        staged_file = hooks_dir / "staged-hook.py"
        staged_file.write_text("# staged\n")
        subprocess.run(["git", "add", str(staged_file)], cwd=str(tmp_path),
                       check=True, capture_output=True)
        r = run_hook({}, cwd=str(tmp_path))
        output = json.loads(r.stdout)
        assert output["decision"] == "block"
        assert "staged-hook.py" in output["reason"]


# ---------------------------------------------------------------------------
# Git error resilience
# ---------------------------------------------------------------------------

class TestGitErrorResilience:
    def test_exits_zero_when_not_a_git_repo(self, tmp_path):
        """Non-git directory must not block — guard exits 0 silently."""
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "block" not in r.stdout

    def test_exits_zero_when_git_not_on_path(self, tmp_path):
        """Missing git binary must not crash or block."""
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path), "PATH": "/nonexistent"}
        r = subprocess.run(
            [sys.executable, HOOK],
            input=json.dumps({}),
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert "block" not in r.stdout

    def test_exits_zero_when_cwd_does_not_exist(self, tmp_path):
        """Non-existent CWD must not crash."""
        r = run_hook({}, cwd="/nonexistent/path/that/does/not/exist")
        assert r.returncode == 0


# ---------------------------------------------------------------------------
# Source-level invariants
# ---------------------------------------------------------------------------

class TestSourceInvariants:
    def test_uses_read_event_from_utils(self):
        source = Path(HOOK).read_text()
        assert "read_event" in source

    def test_uses_get_cwd_from_utils(self):
        source = Path(HOOK).read_text()
        assert "get_cwd" in source

    def test_never_exits_nonzero(self):
        """Hook must not contain sys.exit(1) or any non-zero exit code."""
        source = Path(HOOK).read_text()
        import re
        bad_exits = re.findall(r'sys\.exit\(([^0\)][^)]*)\)', source)
        assert not bad_exits, f"Non-zero exit codes found: {bad_exits}"

    def test_checks_stop_hook_active(self):
        source = Path(HOOK).read_text()
        assert "stop_hook_active" in source
```

Run: `make test-unit` — must FAIL (`hooks/stop-guard.py` does not exist)

### Step 2: Implement (GREEN)

```python
# hooks/stop-guard.py

#!/usr/bin/env python3
"""Stop hook — block if uncommitted implementation files are detected.

Emits {"decision": "block", "reason": "..."} to stdout when git status
reports uncommitted hooks/*.py, tests/*.py, commands/*.md, skills/**/*.md,
or templates/**/* files. Exits 0 on all error paths (ADR-003).

Infinite-loop guard: if event["stop_hook_active"] is truthy, the hook
has already fired once for this continuation cycle — exit immediately
without running git, preventing Claude from being blocked indefinitely.
"""
import fnmatch
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils import read_event, get_cwd

# Canonical implementation file patterns for zie-framework layout.
# Paths are matched against the raw path token from `git status --short`
# (relative to repo root, e.g. "hooks/stop-guard.py").
IMPL_PATTERNS = [
    "hooks/*.py",
    "tests/*.py",
    "commands/*.md",
    "skills/*.md",
    "skills/*/*.md",
    "templates/*",
    "templates/*/*",
    "templates/*/*/*",
]

# ---------------------------------------------------------------------------
# Outer guard — parse stdin; never block Claude on failure
# ---------------------------------------------------------------------------
try:
    event = read_event()
except SystemExit:
    sys.exit(0)

# Infinite-loop guard: Claude Code sets stop_hook_active on the Stop event
# that follows a hook-triggered continuation. Exit immediately so the guard
# fires at most once per original response.
if event.get("stop_hook_active"):
    sys.exit(0)

# ---------------------------------------------------------------------------
# Inner operations — git status + filter
# ---------------------------------------------------------------------------
try:
    cwd = get_cwd()
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=5,
    )
    # Non-zero return code means not a git repo, detached HEAD, or bare repo.
    if result.returncode != 0:
        sys.exit(0)

    uncommitted = []
    for line in result.stdout.splitlines():
        if len(line) < 4:
            continue
        # git status --short format: XY<space>path
        # XY is two chars; char index 0=staged, 1=unstaged; path starts at [3:]
        path_token = line[3:].strip()
        # Strip rename arrows: "old -> new" — take the destination
        if " -> " in path_token:
            path_token = path_token.split(" -> ", 1)[1].strip()
        if any(fnmatch.fnmatch(path_token, pat) for pat in IMPL_PATTERNS):
            uncommitted.append(path_token)

    if not uncommitted:
        sys.exit(0)

    file_list = "\n".join(f"  {p}" for p in sorted(uncommitted))
    reason = (
        f"Uncommitted implementation files detected:\n{file_list}\n\n"
        "Commit this work before ending:\n"
        "  git add -A && git commit -m 'feat: <describe change>'"
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)

except Exception as e:
    print(f"[zie-framework] stop-guard: {e}", file=sys.stderr)
    sys.exit(0)
```

Run: `make test-unit` — must PASS

### Step 3: Refactor

Review and confirm:

- The two-tier error handling is clean: outer guard wraps `read_event()` + `stop_hook_active` check; inner `try/except Exception` wraps all git operations.
- `IMPL_PATTERNS` covers `skills/**/*.md` depth via multiple explicit glob entries (`skills/*.md`, `skills/*/*.md`) — Python's `fnmatch` does not support `**` recursion, so explicit depth entries are the correct approach.
- The rename-arrow stripping handles `git status --short` output for moved files (e.g., `R  old.py -> new.py`).
- Docstring accurately describes the infinite-loop guard mechanism.

Run: `make test-unit` — still PASS

---

## Task 2: Register as first Stop hook in `hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `stop-guard.py` is the first command in the `Stop` hooks list
- `session-learn.py` and `session-cleanup.py` remain in their original order after it
- JSON is valid and all other hook entries are unchanged

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `tests/unit/test_stop_guard.py` (add registration test)

### Step 1: Write failing test (RED)

```python
# tests/unit/test_stop_guard.py — add new class at end of file

class TestHooksJsonRegistration:
    def test_stop_guard_registered_first_in_stop_hooks(self):
        """stop-guard.py must be the first command in the Stop hooks list."""
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        stop_hooks = data["hooks"]["Stop"]
        # Flatten all hook command entries across all matcher groups
        all_commands = []
        for group in stop_hooks:
            for hook in group.get("hooks", []):
                all_commands.append(hook.get("command", ""))
        assert all_commands, "Stop hooks list must not be empty"
        first_cmd = all_commands[0]
        assert "stop-guard.py" in first_cmd, (
            f"stop-guard.py must be the first Stop hook; got: {first_cmd}"
        )

    def test_session_learn_still_registered(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        stop_hooks = data["hooks"]["Stop"]
        all_commands = []
        for group in stop_hooks:
            for hook in group.get("hooks", []):
                all_commands.append(hook.get("command", ""))
        assert any("session-learn.py" in c for c in all_commands)

    def test_session_cleanup_still_registered(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        stop_hooks = data["hooks"]["Stop"]
        all_commands = []
        for group in stop_hooks:
            for hook in group.get("hooks", []):
                all_commands.append(hook.get("command", ""))
        assert any("session-cleanup.py" in c for c in all_commands)

    def test_stop_guard_before_session_learn(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        stop_hooks = data["hooks"]["Stop"]
        all_commands = []
        for group in stop_hooks:
            for hook in group.get("hooks", []):
                all_commands.append(hook.get("command", ""))
        guard_idx = next(i for i, c in enumerate(all_commands) if "stop-guard.py" in c)
        learn_idx = next(i for i, c in enumerate(all_commands) if "session-learn.py" in c)
        assert guard_idx < learn_idx, "stop-guard.py must appear before session-learn.py"
```

Run: `make test-unit` — must FAIL (`stop-guard.py` not yet in `hooks.json`)

### Step 2: Implement (GREEN)

```json
// hooks/hooks.json — updated Stop section only (full file shown for clarity)
{
  "_hook_output_protocol": {
    "SessionStart": "plain text printed to stdout — injected as session context",
    "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
    "PostToolUse": "plain text warnings/status printed to stdout",
    "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
    "Stop": "JSON {\"decision\": \"block\", \"reason\": \"...\"} to stdout to re-invoke Claude; or no output for side-effect-only hooks"
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
            "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stop-guard.py\""
          },
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
    ]
  }
}
```

Note: the `_hook_output_protocol` comment for `Stop` is updated to document the `decision: block` response format, since `stop-guard.py` is the first Stop hook that uses it.

Run: `make test-unit` — must PASS

### Step 3: Refactor

Confirm:
- JSON parses cleanly (`python3 -c "import json; json.load(open('hooks/hooks.json'))"`)
- Hook order in the single `Stop` group is: `stop-guard.py` → `session-learn.py` → `session-cleanup.py`
- All three hooks are in one group (no matcher needed for Stop; consistent with existing structure)

Run: `make test-unit` — still PASS

---

## Task 3: Update `zie-framework/project/components.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `stop-guard.py` row appears in the Hooks table with correct event, trigger, and output columns
- Existing rows are unchanged

**Files:**
- Modify: `zie-framework/project/components.md`

### Step 1: Write failing test (RED)

```python
# tests/unit/test_stop_guard.py — add to TestHooksJsonRegistration class or new class

class TestComponentsDocumented:
    def test_stop_guard_in_components_md(self):
        components = Path(REPO_ROOT) / "zie-framework" / "project" / "components.md"
        content = components.read_text()
        assert "stop-guard.py" in content, (
            "stop-guard.py must be documented in zie-framework/project/components.md"
        )
```

Run: `make test-unit` — must FAIL (`stop-guard.py` not yet in `components.md`)

### Step 2: Implement (GREEN)

Add a row to the Hooks table in `zie-framework/project/components.md`:

```markdown
| `hooks/stop-guard.py` | Stop | Uncommitted implementation files present (hooks, tests, commands, skills, templates) | `{"decision": "block", "reason": "..."}` to stdout; exits 0 |
```

Place it as the first data row under the Hooks table header (before `session-learn.py`), consistent with its position in `hooks.json`.

Run: `make test-unit` — must PASS

### Step 3: Refactor

No structural changes. Confirm table alignment and that the row accurately describes the `stop_hook_active` guard behavior in a prose note if the table has a Notes column; otherwise the row alone is sufficient.

Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/stop-guard.py hooks/hooks.json tests/unit/test_stop_guard.py zie-framework/project/components.md && git commit -m "feat: stop hook uncommitted work guard"`*
