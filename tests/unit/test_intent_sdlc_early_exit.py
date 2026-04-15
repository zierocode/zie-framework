"""Tests for length + keyword early-exit gates in hooks/intent-sdlc.py."""
from __future__ import annotations

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
    """Gate 1: messages under 50 chars without a strong keyword must exit silently."""

    def test_empty_string_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("", tmp_cwd=cwd, session_id="test-lg-empty")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_two_char_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("ok", tmp_cwd=cwd, session_id="test-lg-ok")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_49_char_no_keyword_unclear(self, tmp_path):
        # 49 chars, no SDLC keyword → unclear hint (not silent)
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("x" * 49, tmp_cwd=cwd, session_id="test-lg-49u")
        assert r.returncode == 0
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            assert "unclear" in data.get("additionalContext", "").lower()

    def test_50_char_with_keyword_passes(self, tmp_path):
        # 50+ chars with SDLC keyword — must produce output
        cwd = make_cwd_with_zf(tmp_path)
        msg = "implement this feature that we discussed yesterday please help"
        r = run_hook(msg, tmp_cwd=cwd, session_id="test-lg-50")
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_borderline_with_spaces_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("  ok  ", tmp_cwd=cwd, session_id="test-lg-spaces")
        assert r.returncode == 0
        assert r.stdout.strip() == ""


class TestKeywordGate:
    """Gate 2: messages >= 50 chars with no SDLC keyword must exit silently."""

    def test_no_keyword_long_message_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("what is the weather today over there in the city please", tmp_cwd=cwd, session_id="test-kg-weather")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_url_only_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("https://example.com/some/path/here/that/is/very/long/and/detailed", tmp_cwd=cwd, session_id="test-kg-url")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_generic_question_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("can you explain how async works here in this project", tmp_cwd=cwd, session_id="test-kg-async")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_fix_keyword_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("there is a bug in the auth module that needs fixing now", tmp_cwd=cwd, session_id="test-kg-fix")
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_implement_keyword_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("let us implement this new feature for the project right now", tmp_cwd=cwd, session_id="test-kg-impl")
        assert r.returncode == 0
        assert r.stdout.strip() != ""

    def test_plan_keyword_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("we should plan this backlog item before implementing", tmp_cwd=cwd, session_id="test-kg-plan")
        assert r.returncode == 0
        assert r.stdout.strip() != ""


class TestSlashCommandGate:
    """Gate 3: messages whose first token starts with '/' must exit silently."""

    def test_simple_slash_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("/sprint", tmp_cwd=cwd, session_id="test-sc-sprint")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_slash_with_args_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("/sprint slug1 slug2 --dry-run", tmp_cwd=cwd, session_id="test-sc-sprint-args")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_slash_implement_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("/implement lean-my-feature", tmp_cwd=cwd, session_id="test-sc-impl")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_slash_retro_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("/retro", tmp_cwd=cwd, session_id="test-sc-retro")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_non_slash_implement_passes(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("let us implement this new feature for the project right now", tmp_cwd=cwd, session_id="test-sc-nosl")
        assert r.returncode == 0
        assert r.stdout.strip() != ""


class TestIdleStateSuffix:
    """State suffix omitted when idle + no active task + unambiguous intent."""

    def _parse_context(self, stdout: str) -> str | None:
        import json as _json
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = _json.loads(line)
                if "additionalContext" in obj:
                    return obj["additionalContext"]
            except Exception:
                pass
        return None

    def test_no_state_suffix_when_idle_unambiguous(self, tmp_path):
        """idle + no Now item + strong intent (score>=2) → no state suffix."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook("implement this feature and start coding right now please", tmp_cwd=cwd,
                     session_id="test-idle-unamb")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None, "Expected context output"
        assert "stage:idle" not in ctx
        assert "now:none" not in ctx

    def test_state_suffix_present_when_active_task(self, tmp_path):
        """Active Now item → state suffix always present."""
        roadmap = "## Now\n- [ ] my-feature RED phase\n## Next\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook("implement this feature and start coding now for real", tmp_cwd=cwd,
                     session_id="test-idle-active")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "stage:" in ctx
        assert "now:" in ctx

    def test_state_suffix_present_when_ambiguous(self, tmp_path):
        """idle + low intent score (< 2) → state suffix still present."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook("there is a bug in the authentication module that needs fixing", tmp_cwd=cwd,
                     session_id="test-idle-amb")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "stage:" in ctx


class TestNewIntentCombinedRegex:
    """New-intent scoring via combined regex named groups (≥2 threshold)."""

    def _parse_context(self, stdout: str) -> str | None:
        import json as _json
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = _json.loads(line)
                if "additionalContext" in obj:
                    return obj["additionalContext"]
            except Exception:
                pass
        return None

    def test_sprint_intent_two_signals(self, tmp_path):
        """build + coding (new_sprint) + implement → sprint (≥2 signals)."""
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("let us implement and build this feature start coding right away", tmp_cwd=cwd,
                     session_id="test-ni-sprint2")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "/sprint" in ctx or "sprint" in ctx.lower()

    def test_fix_intent_two_signals(self, tmp_path):
        """broken + crash → fix (2 signals from new_fix group + existing fix group)."""
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("the broken module keeps crashing and throwing errors everywhere", tmp_cwd=cwd,
                     session_id="test-ni-fix2")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "/fix" in ctx or "/hotfix" in ctx

    def test_chore_intent_two_signals(self, tmp_path):
        """cleanup + refactor → chore (2 signals)."""
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("we should cleanup the codebase and refactor the old modules", tmp_cwd=cwd,
                     session_id="test-ni-chore2")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "/chore" in ctx