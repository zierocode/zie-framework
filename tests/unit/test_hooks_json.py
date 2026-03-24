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
