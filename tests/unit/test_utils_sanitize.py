import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from utils_config import load_config
from utils_event import sanitize_log_field


def test_sanitize_newline():
    assert sanitize_log_field("foo\nbar") == "foo?bar"


def test_sanitize_null_byte():
    assert sanitize_log_field("foo\x00bar") == "foo?bar"


def test_sanitize_control_chars():
    assert sanitize_log_field("foo\nbar\x00baz") == "foo?bar?baz"


def test_sanitize_del():
    assert sanitize_log_field("foo\x7fbar") == "foo?bar"


def test_sanitize_none():
    assert sanitize_log_field(None) == "None"


def test_sanitize_int():
    assert sanitize_log_field(42) == "42"


def test_sanitize_clean_string():
    assert sanitize_log_field("safe string") == "safe string"


def test_load_config_malformed_json_returns_empty(tmp_path, capsys):
    config_dir = tmp_path / "zie-framework"
    config_dir.mkdir()
    (config_dir / ".config").write_text("{invalid json}")
    result = load_config(tmp_path)
    assert result["subprocess_timeout_s"] == 5  # defaults filled in
    captured = capsys.readouterr()
    assert "[zie-framework] config parse error:" in captured.err


def test_load_config_missing_file_no_stderr(tmp_path, capsys):
    result = load_config(tmp_path)
    assert result["subprocess_timeout_s"] == 5  # defaults filled in
    captured = capsys.readouterr()
    assert captured.err == ""  # no error for missing file (expected state)


def test_load_config_valid_json(tmp_path):
    config_dir = tmp_path / "zie-framework"
    config_dir.mkdir()
    (config_dir / ".config").write_text('{"test_runner": "pytest"}')
    result = load_config(tmp_path)
    assert result["test_runner"] == "pytest"
    assert result["subprocess_timeout_s"] == 5  # defaults also present
