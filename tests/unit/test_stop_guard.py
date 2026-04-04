"""Tests for hooks/stop-guard.py"""
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOK = os.path.join(REPO_ROOT, "hooks", "stop-guard.py")


def run_hook(event: dict, cwd: str = "/tmp", env_overrides: dict = None):
    # Unique session ID per invocation prevents session cache from bleeding across tests
    env = {**os.environ, "CLAUDE_CWD": cwd, "CLAUDE_SESSION_ID": str(uuid.uuid4())}
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

    def test_missing_tool_name_exits_zero(self, tmp_path):
        """Event with no tool_name key must exit 0."""
        event = {"tool_input": {"command": "echo hello"}}
        r = run_hook(event, cwd=str(tmp_path))
        assert r.returncode == 0

    def test_malformed_event_not_dict_exits_zero(self, tmp_path):
        """stdin containing a JSON string (not a dict) must exit 0."""
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, HOOK],
            input='"just a string"',
            capture_output=True, text=True, env=env,
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

    def test_no_shell_true_in_nudge1(self):
        """Nudge 1 block must not use shell=True (shell injection risk)."""
        source = Path(HOOK).read_text()
        assert "shell=True" not in source, "shell=True must be removed from stop-guard.py"

    def test_no_nosec_b602_annotation(self):
        """nosec B602 annotation must be removed after shell=True is eliminated."""
        source = Path(HOOK).read_text()
        assert "nosec B602" not in source, "# nosec B602 annotation must be removed"

    def test_re_escape_used_in_nudge1(self):
        """re.escape must be used when building the slug pattern (prevents regex injection)."""
        source = Path(HOOK).read_text()
        assert "re.escape" in source, "re.escape(slug) must be used to build the search pattern"

    def test_git_log_uses_list_form(self):
        """git log must be called with a list arg (shell=False) to prevent injection."""
        source = Path(HOOK).read_text()
        assert '"git", "log"' in source or "'git', 'log'" in source, (
            "git log must be called with shell=False list form"
        )

    def test_nudge_gate_uses_cache_helpers(self):
        """stop-guard.py must use get_cached_git_status for the nudge TTL gate."""
        source = Path(HOOK).read_text()
        assert "get_cached_git_status" in source
        assert "write_git_status_cache" in source

    def test_nudge_gate_ttl_is_1800(self):
        """Nudge TTL must be 1800 seconds (30 min)."""
        source = Path(HOOK).read_text()
        assert "ttl=1800" in source, "Nudge gate TTL must be hardcoded to 1800s"

    def test_nudge_gate_key_is_nudge_check(self):
        """Nudge gate cache key must be 'nudge-check'."""
        source = Path(HOOK).read_text()
        assert '"nudge-check"' in source, "Cache key must be 'nudge-check'"


# ---------------------------------------------------------------------------
# hooks.json registration
# ---------------------------------------------------------------------------

class TestHooksJsonRegistration:
    def test_stop_guard_registered_first_in_stop_hooks(self):
        """stop-guard.py must be the first command in the Stop hooks list."""
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        stop_hooks = data["hooks"]["Stop"]
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


# ---------------------------------------------------------------------------
# components.md documentation
# ---------------------------------------------------------------------------

class TestComponentsDocumented:
    def test_stop_guard_in_components_md(self):
        components = Path(REPO_ROOT) / "zie-framework" / "project" / "components.md"
        content = components.read_text()
        assert "stop-guard.py" in content, (
            "stop-guard.py must be documented in zie-framework/project/components.md"
        )


class TestRenameArrowInFilename:
    """stop-guard must not crash or misclassify a file whose name contains ' -> '."""

    def _init_repo(self, tmp_path):
        subprocess.run(["git", "init"], cwd=str(tmp_path), check=True,
                       capture_output=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=str(tmp_path), check=True, capture_output=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.com",
                 "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.com"},
        )

    def test_arrow_in_filename_does_not_crash(self, tmp_path):
        """A file whose name contains ' -> ' must not cause the hook to crash."""
        self._init_repo(tmp_path)
        hooks_dir = tmp_path / "hooks"
        hooks_dir.mkdir()
        arrow_file = hooks_dir / "old -> new.py"
        arrow_file.write_text("# arrow in filename\n")
        r = run_hook({}, cwd=str(tmp_path))
        assert r.returncode == 0
        assert "Traceback" not in r.stderr


class TestStopGuardTimeoutFromConfig:
    def test_subprocess_timeout_s_read_from_config(self):
        """stop-guard.py must read subprocess_timeout_s from validated config."""
        from pathlib import Path
        source = Path(HOOK).read_text()
        assert 'config["subprocess_timeout_s"]' in source, \
            "stop-guard.py must use config['subprocess_timeout_s'], not hardcoded timeout"
        assert "timeout=5" not in source, \
            "hardcoded timeout=5 must be removed from stop-guard.py"
