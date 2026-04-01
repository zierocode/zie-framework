"""
Error-path tests: all hooks must exit 0 when zie-framework/ dir is absent.
Covers the outer guard of the two-tier error handling convention.
"""

import pytest


def _make_edit_event():
    return {"tool_name": "Edit", "tool_input": {"file_path": "/tmp/fake.py"}, "tool_response": "ok"}


def _make_subagent_event():
    return {"agent_type": "Explore"}


@pytest.mark.error_path
def test_intent_sdlc_no_zf_dir(tmp_path, run_hook):
    r = run_hook("intent-sdlc.py", {"prompt": "implement feature X"}, tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_session_resume_no_zf_dir(tmp_path, run_hook):
    r = run_hook("session-resume.py", {}, tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_auto_test_no_zf_dir(tmp_path, run_hook):
    r = run_hook("auto-test.py", _make_edit_event(), tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_sdlc_compact_no_zf_dir(tmp_path, run_hook):
    r = run_hook("sdlc-compact.py", {}, tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_safety_check_no_zf_dir(tmp_path, run_hook):
    r = run_hook("safety-check.py", {"tool_name": "Bash", "tool_input": {"command": "ls"}},
                 tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_subagent_context_no_zf_dir(tmp_path, run_hook):
    r = run_hook("subagent-context.py", _make_subagent_event(), tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_failure_context_no_zf_dir(tmp_path, run_hook):
    r = run_hook("failure-context.py", {"error": "some error", "exit_code": 1}, tmp_cwd=tmp_path)
    assert r.returncode == 0


@pytest.mark.error_path
def test_session_cleanup_no_zf_dir(tmp_path, run_hook):
    r = run_hook("session-cleanup.py", {}, tmp_cwd=tmp_path)
    assert r.returncode == 0
