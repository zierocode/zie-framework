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
