"""Tests for TEST_INDICATORS config path in task-completed-gate.py."""

import importlib.machinery
import json
import types
from pathlib import Path

HOOK = Path(__file__).parents[2] / "hooks" / "task-completed-gate.py"


def _load_hook():
    loader = importlib.machinery.SourceFileLoader("task_completed_gate", str(HOOK))
    mod = types.ModuleType("task_completed_gate")
    mod.__file__ = str(HOOK)
    loader.exec_module(mod)
    return mod


_mod = _load_hook()
_load_test_indicators = _mod._load_test_indicators
_DEFAULT_TEST_INDICATORS = _mod._DEFAULT_TEST_INDICATORS


def test_default_when_config_missing(tmp_path):
    """When .config is absent, returns _DEFAULT_TEST_INDICATORS."""
    result = _load_test_indicators(tmp_path)
    assert result == _DEFAULT_TEST_INDICATORS


def test_custom_indicators_from_config(tmp_path):
    """When config has test_indicators, returns parsed tuple."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    config = {"test_indicators": "test_, _spec., .check."}
    (zf / ".config").write_text(json.dumps(config))
    result = _load_test_indicators(tmp_path)
    assert result == ("test_", "_spec.", ".check.")


def test_empty_string_in_config_falls_back_to_default(tmp_path):
    """Empty string in config must fall back to default — never empty tuple."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    config = {"test_indicators": ""}
    (zf / ".config").write_text(json.dumps(config))
    result = _load_test_indicators(tmp_path)
    assert result == _DEFAULT_TEST_INDICATORS
    assert len(result) > 0, "Gate must never have zero indicators"


def test_whitespace_only_entries_stripped(tmp_path):
    """Whitespace-only entries after split are excluded."""
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    config = {"test_indicators": "test_, , _test."}
    (zf / ".config").write_text(json.dumps(config))
    result = _load_test_indicators(tmp_path)
    assert "" not in result
    assert "test_" in result
    assert "_test." in result
