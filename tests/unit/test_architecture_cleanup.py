"""Tests for architecture-cleanup changes:
- TEST_INDICATORS configurable in task-completed-gate.py
- async hooks in hooks.json
- hook-events.schema.json
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "hooks"))


class TestTestIndicatorsConfigurable:
    def test_load_test_indicators_function_exists(self):
        """task-completed-gate.py must define _load_test_indicators."""
        content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
        assert "_load_test_indicators" in content, "_load_test_indicators not found in task-completed-gate.py"

    def test_module_level_test_indicators_removed(self):
        """Hardcoded module-level TEST_INDICATORS tuple must be removed."""
        content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
        assert not re.search(r"^TEST_INDICATORS\s*=", content, re.MULTILINE), (
            "TEST_INDICATORS must not be a bare module-level assignment"
        )

    def test_fallback_tuple_contains_test_prefix(self):
        """Default fallback must include 'test_' indicator."""
        content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
        assert '"test_"' in content or "'test_'" in content, "fallback tuple must include 'test_'"

    def test_fallback_tuple_contains_test_suffix(self):
        """Default fallback must include '_test.' indicator."""
        content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
        assert '"_test."' in content or "'_test.'" in content, "fallback tuple must include '_test.'"

    def test_load_config_imported(self):
        """load_config must be imported from utils in task-completed-gate.py."""
        content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
        assert "load_config" in content
        assert "from utils import" in content or "from utils_config import" in content

    def test_is_impl_file_still_referenced(self):
        """is_impl_file must still exist in task-completed-gate.py."""
        content = (REPO_ROOT / "hooks" / "task-completed-gate.py").read_text()
        assert "is_impl_file" in content
        assert "TEST_INDICATORS" in content


class TestAsyncStopHooks:
    def _load(self):
        with open(REPO_ROOT / "hooks" / "hooks.json") as f:
            return json.load(f)

    def _stop_hooks(self, data):
        """Return list of hook dicts from the Stop event."""
        return [hook for entry in data["hooks"].get("Stop", []) for hook in entry.get("hooks", [])]

    def test_session_learn_has_background_true(self):
        data = self._load()
        hooks = self._stop_hooks(data)
        session_learn = [h for h in hooks if "session-learn.py" in h.get("command", "")]
        assert session_learn, "session-learn.py not found in Stop hooks"
        assert session_learn[0].get("background") is True, "session-learn.py Stop hook must have background: true"

    def test_session_cleanup_has_background_true(self):
        data = self._load()
        hooks = self._stop_hooks(data)
        session_cleanup = [h for h in hooks if "session-cleanup.py" in h.get("command", "")]
        assert session_cleanup, "session-cleanup.py not found in Stop hooks"
        assert session_cleanup[0].get("background") is True, "session-cleanup.py Stop hook must have background: true"

    def test_stop_guard_is_not_async(self):
        """stop-guard merged into stop-handler.py (v1.29.0 stop-handler-merge)."""
        data = self._load()
        hooks = self._stop_hooks(data)
        stop_handler = [h for h in hooks if "stop-handler.py" in h.get("command", "")]
        assert stop_handler, "stop-handler.py not found in Stop hooks"
        # stop-handler must NOT be async (it may return nudges/decisions)
        assert stop_handler[0].get("async") is not True, (
            "stop-handler.py must NOT be async (it may return nudges/decisions)"
        )

    def test_notification_log_not_async(self):
        data = self._load()
        notification_hooks = [
            hook for entry in data["hooks"].get("Notification", []) for hook in entry.get("hooks", [])
        ]
        for hook in notification_hooks:
            if "notification-log.py" in hook.get("command", ""):
                assert hook.get("async") is not True, "notification-log.py must NOT be async"

    def test_hooks_json_still_valid_json(self):
        self._load()  # must not raise


class TestHookEventsSchema:
    SCHEMA_PATH = REPO_ROOT / "hooks" / "hook-events.schema.json"

    def test_schema_file_exists(self):
        assert self.SCHEMA_PATH.exists(), f"hook-events.schema.json not found at {self.SCHEMA_PATH}"

    def test_schema_is_valid_json(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_schema_version_field(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert data.get("$schema") == "https://json-schema.org/draft/2020-12/schema"

    def test_schema_title(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert data.get("title") == "Claude Code Hook Event Envelope"

    def test_schema_documents_tool_name(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert "tool_name" in data.get("properties", {}), "schema must document tool_name property"

    def test_schema_documents_tool_input(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert "tool_input" in data.get("properties", {})

    def test_schema_documents_tool_response(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert "tool_response" in data.get("properties", {})

    def test_schema_documents_is_interrupt(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert "is_interrupt" in data.get("properties", {})

    def test_schema_documents_session_id(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert "session_id" in data.get("properties", {})

    def test_schema_allows_additional_properties(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert data.get("additionalProperties") is True, (
            "additionalProperties must be true to allow future Claude Code fields"
        )

    def test_schema_type_is_object(self):
        with open(self.SCHEMA_PATH) as f:
            data = json.load(f)
        assert data.get("type") == "object"
