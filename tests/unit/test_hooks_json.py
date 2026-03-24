"""Structural tests for hooks/hooks.json."""
import json
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HOOKS_JSON = os.path.join(REPO_ROOT, "hooks", "hooks.json")


class TestHooksJsonStructure:
    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_posttoolusefailure_key_exists(self):
        data = self._load()
        assert "PostToolUseFailure" in data["hooks"], (
            "PostToolUseFailure entry missing from hooks.json"
        )

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
        assert "PostToolUseFailure" in protocol, (
            "_hook_output_protocol must document PostToolUseFailure"
        )

    def test_existing_hooks_unchanged(self):
        data = self._load()
        hooks = data["hooks"]
        for key in ["SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"]:
            assert key in hooks, f"Existing hook key '{key}' was removed"


class TestHooksJsonSubagentStop:
    def _load(self):
        with open(HOOKS_JSON) as f:
            return json.load(f)

    def test_hooks_json_is_valid_json(self):
        self._load()  # must not raise

    def test_subagent_stop_key_present(self):
        data = self._load()
        assert "SubagentStop" in data["hooks"], (
            "hooks.json must contain a SubagentStop entry"
        )

    def test_subagent_stop_has_async_true(self):
        data = self._load()
        entries = data["hooks"]["SubagentStop"]
        assert len(entries) == 1
        hook = entries[0]["hooks"][0]
        assert hook.get("async") is True, (
            "SubagentStop hook must have async: true"
        )

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
