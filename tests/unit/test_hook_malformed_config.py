"""
Error-path tests: hooks must exit 0 on empty, invalid, or unrecognized .config.
Validates load_config() graceful degradation (returns {} on any error).
"""
import pytest
from pathlib import Path


def _make_zf_dir(tmp_path):
    zf = tmp_path / "zie-framework"
    zf.mkdir(parents=True)
    (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n")
    return tmp_path


@pytest.mark.error_path
def test_empty_config_dict(tmp_path, run_hook):
    cwd = _make_zf_dir(tmp_path)
    (cwd / "zie-framework" / ".config").write_text("{}")
    r = run_hook("session-resume.py", {}, tmp_cwd=cwd)
    assert r.returncode == 0


@pytest.mark.error_path
def test_invalid_json_config(tmp_path, run_hook):
    cwd = _make_zf_dir(tmp_path)
    (cwd / "zie-framework" / ".config").write_text("{ not valid json !!!")
    r = run_hook("session-resume.py", {}, tmp_cwd=cwd)
    assert r.returncode == 0


@pytest.mark.error_path
def test_unrecognized_keys_config(tmp_path, run_hook):
    cwd = _make_zf_dir(tmp_path)
    (cwd / "zie-framework" / ".config").write_text(
        '{"unknown_key": "value", "another_unknown": 42}'
    )
    r = run_hook("intent-sdlc.py", {"prompt": "implement feature X"}, tmp_cwd=cwd)
    assert r.returncode == 0


@pytest.mark.error_path
def test_config_absent_zf_present(tmp_path, run_hook):
    cwd = _make_zf_dir(tmp_path)
    # No .config file — zie-framework/ dir exists
    assert not (cwd / "zie-framework" / ".config").exists()
    r = run_hook("intent-sdlc.py", {"prompt": "fix the bug"}, tmp_cwd=cwd)
    assert r.returncode == 0
