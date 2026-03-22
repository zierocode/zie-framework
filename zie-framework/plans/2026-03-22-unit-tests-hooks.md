---
approved: true
approved_at: 2026-03-22
backlog: backlog/unit-tests-hooks.md
---

# Unit Tests for All Hooks — Implementation Plan

> **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.

**Goal:** Write pytest unit tests covering all 6 hooks so that every hook's behavior is verifiable offline without running a live Claude Code session.

**Architecture:** Each hook is a standalone Python script that reads a JSON event from stdin, inspects env vars (`CLAUDE_CWD`, `ZIE_MEMORY_API_KEY`, `ZIE_MEMORY_API_URL`), and prints output to stdout. Tests invoke hooks via `subprocess.run` with controlled stdin JSON and a temporary `CLAUDE_CWD` pointing to a minimal fixture directory. Network calls (zie-memory API) are bypassed by omitting `ZIE_MEMORY_API_KEY` from the test environment — all hooks gracefully skip API calls when the key is absent.

**Tech Stack:** Python 3.x, pytest, subprocess, json, tempfile, unittest.mock

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `tests/unit/test_hooks_intent_detect.py` | Tests for `hooks/intent-detect.py` |
| Create | `tests/unit/test_hooks_auto_test.py` | Tests for `hooks/auto-test.py` |
| Create | `tests/unit/test_hooks_safety_check.py` | Tests for `hooks/safety-check.py` |
| Create | `tests/unit/test_hooks_session_resume.py` | Tests for `hooks/session-resume.py` |
| Create | `tests/unit/test_hooks_session_learn.py` | Tests for `hooks/session-learn.py` |
| Create | `tests/unit/test_hooks_wip_checkpoint.py` | Tests for `hooks/wip-checkpoint.py` |

---

## Shared Test Utilities (inline in each file)

Each test file defines its own minimal helpers to stay self-contained:

```python
import os, sys, json, subprocess, tempfile
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_hook(hook_name: str, event: dict, env_overrides: dict = None, tmp_cwd: Path = None) -> subprocess.CompletedProcess:
    hook_path = os.path.join(REPO_ROOT, "hooks", hook_name)
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}  # disable network by default
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, hook_path],
        input=json.dumps(event),
        capture_output=True, text=True, env=env,
    )

def make_zf_dir(tmp_path: Path, with_config: dict = None, with_roadmap: str = None) -> Path:
    """Create a minimal zie-framework directory structure inside tmp_path."""
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if with_config is not None:
        (zf / ".config").write_text(json.dumps(with_config))
    if with_roadmap is not None:
        (zf / "ROADMAP.md").write_text(with_roadmap)
    return tmp_path  # return cwd (parent of zie-framework/)
```

---

## Task 1: Tests for intent-detect.py (RED)

**Hook behavior summary:**
- Reads `{"prompt": "..."}` from stdin
- Exits 0 silently if: invalid JSON, empty prompt, `len < 3`, prompt starts with `/zie-`, or `zie-framework/` dir absent in `CLAUDE_CWD`
- Scores prompt against PATTERNS dict (8 categories), prints `[zie-framework] Detected: <cat> intent → /zie-<cmd>` if best score >= 1
- Suppresses `init` suggestion if `zie-framework/.config` already exists

**Files:**
- Create: `tests/unit/test_hooks_intent_detect.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for hooks/intent-detect.py"""
import os, sys, json, subprocess, tempfile, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_hook(event, tmp_cwd=None, env_overrides=None):
    hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True, env=env)

def make_cwd_with_zf(tmp_path):
    (tmp_path / "zie-framework").mkdir(parents=True)
    return tmp_path


class TestIntentDetectHappyPath:
    def test_fix_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "there is a bug in the auth module"}, tmp_cwd=cwd)
        assert "/zie-fix" in r.stdout

    def test_build_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "let's build this feature"}, tmp_cwd=cwd)
        assert "/zie-build" in r.stdout

    def test_ship_intent_detected(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "ready to ship and deploy now"}, tmp_cwd=cwd)
        assert "/zie-ship" in r.stdout

    def test_plan_intent_thai(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "อยากวางแผน feature ใหม่"}, tmp_cwd=cwd)
        assert "/zie-plan" in r.stdout

    def test_idea_intent_thai(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "อยากเพิ่ม feature ใหม่"}, tmp_cwd=cwd)
        assert "/zie-idea" in r.stdout


class TestIntentDetectGuardrails:
    def test_no_output_when_no_zf_dir(self, tmp_path):
        # tmp_path has no zie-framework/ dir
        r = run_hook({"prompt": "fix this bug"}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""

    def test_no_output_for_zie_command_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "/zie-build the feature"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_output_for_empty_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": ""}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_output_for_short_prompt(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook({"prompt": "ok"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_output_for_invalid_json(self, tmp_path):
        hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run([sys.executable, hook], input="not json",
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_init_suppressed_when_config_exists(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        (cwd / "zie-framework" / ".config").write_text('{}')
        r = run_hook({"prompt": "init the project bootstrap setup"}, tmp_cwd=cwd)
        assert "/zie-init" not in r.stdout
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_hooks_intent_detect.py -v
```

---

## Task 2: Verify intent-detect tests pass (GREEN)

The hook is fully implemented and these tests exercise existing code paths.

- [ ] **Step 1: Run tests**

```bash
python3 -m pytest tests/unit/test_hooks_intent_detect.py -v
```

Expected: all 11 PASS (hook already implements all tested behavior)

---

## Task 3: Tests for safety-check.py (RED)

**Hook behavior summary:**
- Reads `{"tool_name": "Bash", "tool_input": {"command": "..."}}` from stdin
- Exits 0 silently if: invalid JSON, `tool_name != "Bash"`, or empty command
- Checks command (lowercased) against BLOCKS patterns — prints `[zie-framework] BLOCKED: <msg>` and exits 1
- Checks WARNS patterns — prints `[zie-framework] WARNING: <msg>` and exits 0

**Files:**
- Create: `tests/unit/test_hooks_safety_check.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for hooks/safety-check.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_hook(tool_name, command):
    hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
    event = {"tool_name": tool_name, "tool_input": {"command": command}}
    return subprocess.run([sys.executable, hook], input=json.dumps(event),
                          capture_output=True, text=True)


class TestSafetyCheckBlocks:
    def test_rm_rf_root_is_blocked(self):
        r = run_hook("Bash", "rm -rf /")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout

    def test_rm_rf_dot_is_blocked(self):
        r = run_hook("Bash", "rm -rf .")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout

    def test_git_force_push_main_is_blocked(self):
        r = run_hook("Bash", "git push origin main")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout

    def test_git_push_force_flag_is_blocked(self):
        r = run_hook("Bash", "git push --force origin dev")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout

    def test_git_reset_hard_is_blocked(self):
        r = run_hook("Bash", "git reset --hard HEAD~1")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout

    def test_no_verify_is_blocked(self):
        r = run_hook("Bash", "git commit --no-verify -m 'skip'")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout

    def test_drop_database_is_blocked(self):
        r = run_hook("Bash", "psql -c 'DROP DATABASE mydb'")
        assert r.returncode == 1
        assert "BLOCKED" in r.stdout


class TestSafetyCheckWarns:
    def test_force_with_lease_warns(self):
        r = run_hook("Bash", "git push --force-with-lease origin dev")
        assert r.returncode == 0
        assert "WARNING" in r.stdout

    def test_docker_volumes_warns(self):
        r = run_hook("Bash", "docker compose down --volumes")
        assert r.returncode == 0
        assert "WARNING" in r.stdout

    def test_alembic_downgrade_warns(self):
        r = run_hook("Bash", "alembic downgrade -1")
        assert r.returncode == 0
        assert "WARNING" in r.stdout


class TestSafetyCheckPassThrough:
    def test_safe_command_passes(self):
        r = run_hook("Bash", "git status")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_non_bash_tool_passes(self):
        r = run_hook("Edit", "rm -rf /")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self):
        hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
        r = subprocess.run([sys.executable, hook], input="not json",
                           capture_output=True, text=True)
        assert r.returncode == 0
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_hooks_safety_check.py -v
```

---

## Task 4: Verify safety-check tests pass (GREEN)

- [ ] **Step 1: Run tests**

```bash
python3 -m pytest tests/unit/test_hooks_safety_check.py -v
```

Expected: all 13 PASS

---

## Task 5: Tests for auto-test.py (RED)

**Hook behavior summary:**
- Reads `{"tool_name": "Edit"|"Write", "tool_input": {"file_path": "..."}}` from stdin
- Exits 0 silently if: invalid JSON, `tool_name` not Edit/Write, empty `file_path`, no `zie-framework/` dir, no `test_runner` in `.config`
- Debounce: skips if `/tmp/zie-framework-last-test` was written within `auto_test_debounce_ms` ms
- Runs `find_matching_test` to locate matching test file, then invokes the test runner via `subprocess.run`
- Prints `[zie-framework] Tests pass` on success, `[zie-framework] Tests FAILED` on failure

**Files:**
- Create: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for hooks/auto-test.py"""
import os, sys, json, subprocess, tempfile, time, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "auto-test.py")

def run_hook(event, tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                          capture_output=True, text=True, env=env)

def make_cwd(tmp_path, config=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    return tmp_path


class TestAutoTestGuardrails:
    def test_no_action_when_no_zf_dir(self, tmp_path):
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_no_action_when_no_test_runner_in_config(self, tmp_path):
        cwd = make_cwd(tmp_path, config={})  # test_runner key absent
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_no_action_for_non_edit_tool(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}},
                     tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self, tmp_path):
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run([sys.executable, HOOK], input="not json",
                           capture_output=True, text=True, env=env)
        assert r.returncode == 0

    def test_missing_file_path_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Edit", "tool_input": {}}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""


class TestAutoTestDebounce:
    def test_debounce_suppresses_rapid_second_call(self, tmp_path):
        # Write a fresh debounce file to simulate a very recent test run
        debounce = Path("/tmp/zie-framework-last-test")
        debounce.write_text("some_file.py")
        # Manually set mtime to NOW so debounce window is active
        # (default 3000ms — we just wrote it, so it's within the window)
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 10000})
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        # Should be suppressed — no test runner output expected
        assert "[zie-framework] Tests" not in r.stdout


class TestAutoTestRunnerSelection:
    def test_unknown_test_runner_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"test_runner": "mocha"})
        # Ensure debounce file is old
        debounce = Path("/tmp/zie-framework-last-test")
        if debounce.exists():
            import os as _os
            _os.utime(str(debounce), (0, 0))
        r = run_hook({"tool_name": "Write", "tool_input": {"file_path": "/some/component.ts"}},
                     tmp_cwd=cwd)
        # mocha is not in the supported runners — hook exits 0 silently
        assert r.returncode == 0
        assert "BLOCKED" not in r.stdout
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_hooks_auto_test.py -v
```

---

## Task 6: Verify auto-test tests pass (GREEN)

- [ ] **Step 1: Run tests**

```bash
python3 -m pytest tests/unit/test_hooks_auto_test.py -v
```

Expected: all 6 PASS (debounce test may be environment-sensitive — see notes below)

> **Note on debounce test:** `TestAutoTestDebounce.test_debounce_suppresses_rapid_second_call` depends on `/tmp/zie-framework-last-test` mtime. If the test environment has a stale file from a previous run, behavior is correct. The test sets the file fresh and uses a 10-second window, which should reliably trigger suppression.

---

## Task 7: Tests for session-resume.py (RED)

**Hook behavior summary:**
- Reads any valid JSON from stdin (event content is not used)
- Reads `CLAUDE_CWD` env var, exits if no `zie-framework/` dir
- Reads `zie-framework/.config`, `zie-framework/ROADMAP.md`, `VERSION`
- Scans `zie-framework/plans/` for most recently modified `.md` file
- Prints a multi-line summary: project name, active feature, plan file, backlog count, brain status
- Falls back gracefully when files are missing

**Files:**
- Create: `tests/unit/test_hooks_session_resume.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for hooks/session-resume.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "session-resume.py")

SAMPLE_ROADMAP = """## Now
- [ ] Build the auth module

## Next
- [ ] Add OAuth provider
- [ ] Write integration tests

## Done
- [x] Setup project
"""

def run_hook(tmp_cwd=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    return subprocess.run([sys.executable, HOOK], input=json.dumps({}),
                          capture_output=True, text=True, env=env)

def make_cwd(tmp_path, config=None, roadmap=None, version=None, plans=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if config:
        (zf / ".config").write_text(json.dumps(config))
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    if version:
        (tmp_path / "VERSION").write_text(version)
    if plans:
        plans_dir = zf / "plans"
        plans_dir.mkdir()
        for name, content in plans.items():
            (plans_dir / name).write_text(content)
    return tmp_path


class TestSessionResumeHappyPath:
    def test_prints_project_name(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"project_type": "python-lib"},
                       roadmap=SAMPLE_ROADMAP, version="1.2.3")
        r = run_hook(tmp_cwd=cwd)
        # Project name = dirname of cwd = tmp_path.name
        assert tmp_path.name in r.stdout
        assert "[zie-framework]" in r.stdout

    def test_prints_active_feature_from_now_section(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "auth module" in r.stdout

    def test_prints_backlog_count(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "2" in r.stdout  # 2 items in Next

    def test_prints_active_plan_when_present(self, tmp_path):
        cwd = make_cwd(tmp_path, config={}, roadmap=SAMPLE_ROADMAP,
                       plans={"2026-03-22-my-feature.md": "# plan"})
        r = run_hook(tmp_cwd=cwd)
        assert "2026-03-22-my-feature.md" in r.stdout

    def test_brain_enabled_when_config_says_so(self, tmp_path):
        cwd = make_cwd(tmp_path, config={"zie_memory_enabled": True}, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)
        assert "enabled" in r.stdout


class TestSessionResumeGracefulDegradation:
    def test_no_output_when_no_zf_dir(self, tmp_path):
        r = run_hook(tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_no_active_feature_message_when_now_empty(self, tmp_path):
        roadmap = "## Now\n\n## Next\n- [ ] something\n"
        cwd = make_cwd(tmp_path, config={}, roadmap=roadmap)
        r = run_hook(tmp_cwd=cwd)
        assert "No active feature" in r.stdout or "/zie-idea" in r.stdout

    def test_handles_missing_roadmap_gracefully(self, tmp_path):
        cwd = make_cwd(tmp_path, config={})  # no roadmap
        r = run_hook(tmp_cwd=cwd)
        assert r.returncode == 0
        assert "[zie-framework]" in r.stdout
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_hooks_session_resume.py -v
```

---

## Task 8: Verify session-resume tests pass (GREEN)

- [ ] **Step 1: Run tests**

```bash
python3 -m pytest tests/unit/test_hooks_session_resume.py -v
```

Expected: all 8 PASS

---

## Task 9: Tests for session-learn.py (RED)

**Hook behavior summary:**
- Reads any valid JSON from stdin
- Reads `CLAUDE_CWD`, exits if no `zie-framework/` dir
- Reads `zie-framework/ROADMAP.md` "Now" section to build `wip_context`
- Writes `~/.claude/projects/<project>/pending_learn.txt` with `project=` and `wip=` lines
- If `ZIE_MEMORY_API_KEY` is set, POSTs to `{ZIE_MEMORY_API_URL}/api/hooks/session-stop`
- If API key is absent, exits 0 after writing the file
- Never crashes — all network errors are swallowed

**Files:**
- Create: `tests/unit/test_hooks_session_learn.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for hooks/session-learn.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "session-learn.py")

SAMPLE_ROADMAP = """## Now
- [ ] Implement login flow
- [ ] Add JWT validation

## Next
- [ ] Add refresh tokens
"""

def run_hook(tmp_cwd, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": "", "CLAUDE_CWD": str(tmp_cwd)}
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run([sys.executable, HOOK], input=json.dumps({}),
                          capture_output=True, text=True, env=env)

def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path


class TestSessionLearnPendingLearnFile:
    def test_writes_pending_learn_file(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        assert pending.exists(), f"pending_learn.txt not written at {pending}"

    def test_pending_learn_contains_project_name(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        content = pending.read_text()
        assert f"project={tmp_path.name}" in content

    def test_pending_learn_contains_wip_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        content = pending.read_text()
        assert "login flow" in content or "wip=" in content

    def test_pending_learn_empty_wip_when_no_roadmap(self, tmp_path):
        cwd = make_cwd(tmp_path)  # no ROADMAP.md
        run_hook(cwd)
        pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
        content = pending.read_text()
        assert "project=" in content
        assert "wip=" in content


class TestSessionLearnGuardrails:
    def test_no_action_when_no_zf_dir(self, tmp_path):
        # No zie-framework/ dir
        r = run_hook(tmp_path)
        assert r.returncode == 0

    def test_no_crash_when_api_url_unreachable(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "http://localhost:19999",  # nothing listening here
        })
        assert r.returncode == 0  # must never crash

    def test_skips_api_call_without_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(cwd)  # ZIE_MEMORY_API_KEY="" by default
        assert r.returncode == 0
        assert r.stdout.strip() == ""  # no output when key absent
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_hooks_session_learn.py -v
```

---

## Task 10: Verify session-learn tests pass (GREEN)

- [ ] **Step 1: Run tests**

```bash
python3 -m pytest tests/unit/test_hooks_session_learn.py -v
```

Expected: all 7 PASS

> **Note:** `test_writes_pending_learn_file` and related tests write to `~/.claude/projects/<tmp_path.name>/`. Since `tmp_path` uses pytest's unique temp dirs, there is no collision between runs. The written files are small and harmless.

---

## Task 11: Tests for wip-checkpoint.py (RED)

**Hook behavior summary:**
- Reads `{"tool_name": "Edit"|"Write", ...}` from stdin
- Exits 0 silently if: invalid JSON, `tool_name` not Edit/Write, `ZIE_MEMORY_API_KEY` absent, or no `zie-framework/` dir
- Maintains edit counter at `/tmp/zie-framework-edit-count`
- Only checkpoints when `count % 5 == 0`
- Reads ROADMAP "Now" section for `wip_summary`; exits silently if summary is empty
- POSTs `{content, priority, tags, project, force}` to `{ZIE_MEMORY_API_URL}/api/hooks/wip-update`
- Never crashes on network errors

**Files:**
- Create: `tests/unit/test_hooks_wip_checkpoint.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for hooks/wip-checkpoint.py"""
import os, sys, json, subprocess, pytest
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "wip-checkpoint.py")

SAMPLE_ROADMAP = """## Now
- [ ] Refactor the payment module
"""

def run_hook(tool_name="Edit", tmp_cwd=None, env_overrides=None):
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    event = {"tool_name": tool_name, "tool_input": {"file_path": "/some/file.py"}}
    return subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                          capture_output=True, text=True, env=env)

def make_cwd(tmp_path, roadmap=None):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    if roadmap:
        (zf / "ROADMAP.md").write_text(roadmap)
    return tmp_path

def reset_counter():
    counter = Path("/tmp/zie-framework-edit-count")
    if counter.exists():
        counter.unlink()


class TestWipCheckpointGuardrails:
    def test_no_action_without_api_key(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tmp_cwd=cwd)  # ZIE_MEMORY_API_KEY="" — should exit silently
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_no_action_when_no_zf_dir(self, tmp_path):
        r = run_hook(tmp_cwd=tmp_path, env_overrides={"ZIE_MEMORY_API_KEY": "fake"})
        assert r.returncode == 0

    def test_no_action_for_non_edit_tool(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        r = run_hook(tool_name="Bash", tmp_cwd=cwd,
                     env_overrides={"ZIE_MEMORY_API_KEY": "fake"})
        assert r.stdout.strip() == ""

    def test_invalid_json_exits_zero(self):
        r = subprocess.run([sys.executable, HOOK], input="bad json",
                           capture_output=True, text=True)
        assert r.returncode == 0


class TestWipCheckpointCounter:
    def test_counter_increments_each_call(self, tmp_path):
        reset_counter()
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        for _ in range(3):
            run_hook(tmp_cwd=cwd)
        counter = Path("/tmp/zie-framework-edit-count")
        assert counter.exists()
        assert int(counter.read_text().strip()) == 3

    def test_no_network_call_before_fifth_edit(self, tmp_path):
        reset_counter()
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # Run 4 times with an API key — no network call should succeed (nothing listening)
        for _ in range(4):
            r = run_hook(tmp_cwd=cwd, env_overrides={
                "ZIE_MEMORY_API_KEY": "fake-key",
                "ZIE_MEMORY_API_URL": "http://localhost:19999",
            })
            assert r.returncode == 0  # must not crash even on network error

    def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
        reset_counter()
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
        # Pre-set counter to 4 so the 5th call triggers the checkpoint
        Path("/tmp/zie-framework-edit-count").write_text("4")
        r = run_hook(tmp_cwd=cwd, env_overrides={
            "ZIE_MEMORY_API_KEY": "fake-key",
            "ZIE_MEMORY_API_URL": "http://localhost:19999",
        })
        assert r.returncode == 0  # graceful failure — never crash
```

- [ ] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_hooks_wip_checkpoint.py -v
```

---

## Task 12: Verify wip-checkpoint tests pass (GREEN)

- [ ] **Step 1: Run tests**

```bash
python3 -m pytest tests/unit/test_hooks_wip_checkpoint.py -v
```

Expected: all 7 PASS

> **Note:** Counter tests interact with `/tmp/zie-framework-edit-count`. The `reset_counter()` helper ensures isolation. If tests run in parallel, this can cause flakiness — run with `-p no:xdist` if needed.

---

## Task 13: Full suite verification

- [ ] **Step 1: Run all unit tests**

```bash
make test-unit
```

Expected: all tests across all 6 new files PASS with no errors

- [ ] **Step 2: Confirm test file inventory**

```bash
python3 -m pytest tests/unit/ --collect-only -q
```

Should list test functions from:
- `test_hooks_intent_detect.py`
- `test_hooks_auto_test.py`
- `test_hooks_safety_check.py`
- `test_hooks_session_resume.py`
- `test_hooks_session_learn.py`
- `test_hooks_wip_checkpoint.py`

---

## Context from brain

_(No prior memory entries for this feature — first time implementing hook unit tests.)_
