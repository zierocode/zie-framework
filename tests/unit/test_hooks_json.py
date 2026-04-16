"""Structural tests for hooks/hooks.json."""

import json
import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOKS_JSON = os.path.join(REPO_ROOT, "hooks", "hooks.json")


class TestHooksJsonStructure:
    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_posttoolusefailure_key_exists(self):
        data = self._load()
        assert "PostToolUseFailure" in data["hooks"], "PostToolUseFailure entry missing from hooks.json"

    def test_posttoolusefailure_matcher(self):
        data = self._load()
        entry = data["hooks"]["PostToolUseFailure"][0]
        assert entry["matcher"] == "Bash|Write|Edit"

    def test_posttoolusefailure_command_path(self):
        data = self._load()
        entry = data["hooks"]["PostToolUseFailure"][0]
        cmd = entry["hooks"][0]["command"]
        assert "failure-context.py" in cmd
        assert "${CLAUDE_PLUGIN_ROOT}" in cmd

    def test_hook_output_protocol_documents_posttoolusefailure(self):
        data = self._load()
        protocol = data.get("_hook_output_protocol", {})
        assert "PostToolUseFailure" in protocol, "_hook_output_protocol must document PostToolUseFailure"

    def test_existing_hooks_unchanged(self):
        data = self._load()
        hooks = data["hooks"]
        for key in ["SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"]:
            assert key in hooks, f"Existing hook key '{key}' was removed"


class TestHooksJsonTaskCompleted:
    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_taskcompleted_key_present(self):
        data = self._load()
        assert "TaskCompleted" in data["hooks"], "TaskCompleted entry missing from hooks.json"

    def test_taskcompleted_command_uses_plugin_root(self):
        data = self._load()
        entry = data["hooks"]["TaskCompleted"]
        command = entry[0]["hooks"][0]["command"]
        assert "${CLAUDE_PLUGIN_ROOT}" in command

    def test_taskcompleted_command_references_correct_script(self):
        data = self._load()
        entry = data["hooks"]["TaskCompleted"]
        command = entry[0]["hooks"][0]["command"]
        assert "task-completed-gate.py" in command

    def test_taskcompleted_hook_type_is_command(self):
        data = self._load()
        entry = data["hooks"]["TaskCompleted"]
        assert entry[0]["hooks"][0]["type"] == "command"

    def test_hook_output_protocol_has_taskcompleted(self):
        data = self._load()
        assert "TaskCompleted" in data["_hook_output_protocol"]

    def test_hook_output_protocol_taskcompleted_mentions_exit2(self):
        data = self._load()
        annotation = data["_hook_output_protocol"]["TaskCompleted"]
        assert "exit(2)" in annotation or "2" in annotation

    def test_existing_hooks_unchanged(self):
        data = self._load()
        hooks = data["hooks"]
        for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert key in hooks, f"Existing hook key missing: {key}"


class TestHooksJsonSubagentStop:
    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_hooks_json_is_valid_json(self):
        self._load()  # must not raise

    def test_subagent_stop_key_present(self):
        data = self._load()
        assert "SubagentStop" in data["hooks"], "hooks.json must contain a SubagentStop entry"

    def test_subagent_stop_has_background_true(self):
        data = self._load()
        entries = data["hooks"]["SubagentStop"]
        assert len(entries) == 1
        hook = entries[0]["hooks"][0]
        assert hook.get("background") is True, "SubagentStop hook must have background: true"

    def test_subagent_stop_command_references_correct_script(self):
        data = self._load()
        hook = data["hooks"]["SubagentStop"][0]["hooks"][0]
        assert "subagent-stop.py" in hook["command"]
        assert "${CLAUDE_PLUGIN_ROOT}" in hook["command"]

    def test_existing_hooks_still_present(self):
        data = self._load()
        hooks = data["hooks"]
        for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert key in hooks, f"existing hook key missing: {key}"

    def test_subagent_stop_has_matcher_note(self):
        """SubagentStop entry must document why no matcher is used."""
        data = self._load()
        entry = data["hooks"]["SubagentStop"][0]
        assert "_matcher_note" in entry, (
            "SubagentStop entry must have _matcher_note documenting that matchers are unsupported"
        )
        assert "matcher" in entry["_matcher_note"].lower(), "_matcher_note must explain the matcher limitation"

    def test_subagent_stop_project_guard_in_hook(self):
        """subagent-stop.py must have a project guard (not rely on matcher)."""
        hook_path = Path(HOOKS_JSON).parent / "subagent-stop.py"
        text = hook_path.read_text()
        assert "zie-framework" in text and ("is_dir" in text or "exists" in text), (
            "subagent-stop.py must guard against non-zie-framework projects internally"
        )


class TestHooksJsonSessionLearnCleanup:
    """Test async→background fix for Stop hooks."""

    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_session_learn_has_background_true(self):
        data = self._load()
        entries = data["hooks"]["Stop"]
        learn_entries = [h for e in entries for h in e["hooks"] if "session-learn.py" in h["command"]]
        assert len(learn_entries) == 1, "session-learn.py not found in Stop hooks"
        assert learn_entries[0].get("background") is True, "session-learn.py must have background: true"

    def test_session_cleanup_has_background_true(self):
        data = self._load()
        entries = data["hooks"]["Stop"]
        cleanup_entries = [h for e in entries for h in e["hooks"] if "session-cleanup.py" in h["command"]]
        assert len(cleanup_entries) == 1, "session-cleanup.py not found in Stop hooks"
        assert cleanup_entries[0].get("background") is True, "session-cleanup.py must have background: true"

    def test_no_async_true_in_stop_hooks(self):
        """async: true should not exist in Stop hooks (was replaced by background: true)."""
        data = self._load()
        entries = data["hooks"]["Stop"]
        async_keys = [h.get("async") for e in entries for h in e["hooks"]]
        # None of them should be True
        assert not any(async_keys), "Found async: true in Stop hooks - should be background: true"


class TestHooksJsonSafetyCheckAgent:
    """safety_check_agent.py is imported by safety-check.py — NOT a standalone hook."""

    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def _pretooluse_commands(self, data):
        """Return all command strings from PreToolUse hooks."""
        return [hook["command"] for entry in data["hooks"].get("PreToolUse", []) for hook in entry.get("hooks", [])]

    def test_safety_check_agent_not_in_pretooluse(self):
        """safety_check_agent.py must NOT be registered as a standalone PreToolUse hook."""
        data = self._load()
        commands = self._pretooluse_commands(data)
        assert not any("safety_check_agent.py" in cmd for cmd in commands), (
            "safety_check_agent.py must be imported by safety-check.py, "
            "not registered as a standalone PreToolUse hook (eliminates per-Bash double-fire)"
        )

    def test_only_one_pretooluse_entry_for_bash(self):
        """Only one PreToolUse hook entry fires on Bash events."""
        data = self._load()
        bash_entries = [e for e in data["hooks"].get("PreToolUse", []) if "Bash" in e.get("matcher", "")]
        assert len(bash_entries) == 1, f"Expected exactly 1 PreToolUse entry matching Bash, found {len(bash_entries)}"

    def test_safety_check_agent_script_exists(self):
        script = os.path.join(REPO_ROOT, "hooks", "safety_check_agent.py")
        assert os.path.exists(script), f"Hook script not found: {script}"

    def test_safety_check_imports_agent_module(self):
        """safety-check.py must import safety_check_agent for inline dispatch."""
        content = Path(os.path.join(REPO_ROOT, "hooks", "safety-check.py")).read_text()
        assert "safety_check_agent" in content, (
            "safety-check.py must import/reference safety_check_agent for inline agent dispatch"
        )


class TestHooksJsonWipCheckpointBackground:
    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_wip_checkpoint_is_background(self):
        data = self._load()
        post_tool_hooks = data["hooks"]["PostToolUse"]
        wip_entries = [h for group in post_tool_hooks for h in group["hooks"] if "wip-checkpoint" in h["command"]]
        assert len(wip_entries) == 1, "Expected exactly one wip-checkpoint PostToolUse entry"
        assert wip_entries[0].get("background") is True, (
            "wip-checkpoint must have background: true to avoid blocking Claude on every file save"
        )
