"""Tests for length + keyword early-exit gates in hooks/intent-sdlc.py."""
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def run_hook(prompt: str, tmp_cwd=None, session_id: str = "test-early-exit") -> subprocess.CompletedProcess:
    hook = os.path.join(REPO_ROOT, "hooks", "intent-sdlc.py")
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    event = {"session_id": session_id, "prompt": prompt}
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def make_cwd_with_zf(tmp_path, roadmap_content: str = "## Now\n\n## Next\n"):
    (tmp_path / "zie-framework").mkdir(parents=True)
    (tmp_path / "zie-framework" / "ROADMAP.md").write_text(roadmap_content)
    return tmp_path


class TestLengthGate:
    """Gate 1: messages with len(message.strip()) < 15 must exit silently."""

    def test_empty_string_exits(self, tmp_path):
        # Caught by outer guard (len < 3) — stdout must be empty
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("", tmp_cwd=cwd, session_id="test-lg-empty")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_two_char_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("ok", tmp_cwd=cwd, session_id="test-lg-ok")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_14_char_exits(self, tmp_path):
        # "implement this" = 14 chars — must exit silently
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("implement this", tmp_cwd=cwd, session_id="test-lg-14")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_15_char_passes(self, tmp_path):
        # "implement this!" = 15 chars, has SDLC keyword — must produce output
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("implement this!", tmp_cwd=cwd, session_id="test-lg-15")
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_borderline_with_spaces_exits(self, tmp_path):
        # "  ok  " strips to "ok" (2 chars) — must exit silently
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("  ok  ", tmp_cwd=cwd, session_id="test-lg-spaces")
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestKeywordGate:
    """Gate 2: messages >= 15 chars with no SDLC keyword must exit silently."""

    def test_no_keyword_long_message_exits(self, tmp_path):
        # 36 chars, no SDLC keyword
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("what is the weather today over there", tmp_cwd=cwd, session_id="test-kg-weather")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_url_only_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("https://example.com/some/path/here", tmp_cwd=cwd, session_id="test-kg-url")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_generic_question_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("can you explain how async works here", tmp_cwd=cwd, session_id="test-kg-async")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_fix_keyword_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("there is a bug in the auth module", tmp_cwd=cwd, session_id="test-kg-fix")
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_implement_keyword_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("let us implement this feature now", tmp_cwd=cwd, session_id="test-kg-impl")
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_plan_keyword_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("we should plan this backlog item", tmp_cwd=cwd, session_id="test-kg-plan")
        assert r.returncode == 0
        assert r.stdout.strip() != ""
