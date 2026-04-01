"""Tests for hooks/config-drift.py"""
import json
import os
import subprocess
import sys

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
        path = str(tmp_path / "config" / "settings.json")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


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
        assert "reload" in ctx.lower() or "resync" in ctx.lower()

    def test_dot_config_outside_zie_framework_is_silent(self, tmp_path):
        path = str(tmp_path / "other-dir" / ".config")
        r = run_hook({"hook_event_name": "ConfigChange", "file_path": path}, tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == ""


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
