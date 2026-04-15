"""Tests for utils_error.log_error helper."""
import sys

sys.path.insert(0, "hooks")
from utils_error import log_error


def test_log_error_writes_to_stderr(capsys):
    """log_error writes formatted message to stderr."""
    log_error("stop-handler", "git_status", OSError("no such file"))
    captured = capsys.readouterr()
    assert "[zie-framework] stop-handler: git_status failed — no such file" in captured.err


def test_log_error_format_includes_all_parts(capsys):
    """log_error message includes hook name, operation, and exception message."""
    exc = ValueError("bad input")
    log_error("session-resume", "parse_config", exc)
    captured = capsys.readouterr()
    assert "session-resume" in captured.err
    assert "parse_config" in captured.err
    assert "bad input" in captured.err


def test_log_error_does_not_write_to_stdout(capsys):
    """log_error only writes to stderr, not stdout."""
    log_error("intent-sdlc", "cache_read", RuntimeError("fail"))
    captured = capsys.readouterr()
    assert captured.out == ""


def test_log_error_preserves_exception_type(capsys):
    """log_error preserves the exception type in the message."""
    log_error("sdlc-compact", "roadmap_read", FileNotFoundError("missing.md"))
    captured = capsys.readouterr()
    assert "missing.md" in captured.err


def test_log_error_with_empty_message(capsys):
    """log_error handles exceptions with empty messages."""
    log_error("auto-test", "hash_compute", OSError())
    captured = capsys.readouterr()
    assert "[zie-framework] auto-test: hash_compute failed —" in captured.err