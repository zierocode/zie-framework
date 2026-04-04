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


class TestSlashCommandGate:
    """Gate 3: messages whose first token starts with '/' must exit silently (mid-command)."""

    def test_simple_slash_exits(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("/sprint", tmp_cwd=cwd, session_id="test-sc-sprint")
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_slash_with_args_exits(self, tmp_path):
        # Long command — old guard (< 20 chars) would NOT have caught this
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
        # A message mentioning implement that is NOT a slash command must still pass
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("let us implement this feature now", tmp_cwd=cwd, session_id="test-sc-nosl")
        assert r.returncode == 0
        assert r.stdout.strip() != ""


class TestIdleStateSuffix:
    """State suffix (task/stage/next/tests) omitted when idle + no active task + unambiguous intent."""

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
        # Multiple implement keywords → score >= 2
        r = run_hook("implement this feature and start coding now", tmp_cwd=cwd,
                     session_id="test-idle-unamb")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None, "Expected context output"
        assert "stage:idle" not in ctx, (
            f"State suffix must be suppressed when idle+unambiguous, got: {ctx!r}"
        )
        assert "task:none" not in ctx, (
            f"State suffix must be suppressed when idle+unambiguous, got: {ctx!r}"
        )

    def test_state_suffix_present_when_active_task(self, tmp_path):
        """Active Now item → state suffix always present."""
        roadmap = "## Now\n- [ ] my-feature RED phase\n## Next\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        r = run_hook("implement this feature and start coding now", tmp_cwd=cwd,
                     session_id="test-idle-active")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "stage:" in ctx, f"State suffix missing with active task: {ctx!r}"
        assert "task:" in ctx, f"State suffix missing with active task: {ctx!r}"

    def test_state_suffix_present_when_ambiguous(self, tmp_path):
        """idle + low intent score (< 2) → state suffix still present."""
        roadmap = "## Now\n\n## Next\n- [ ] my-feature\n"
        cwd = make_cwd_with_zf(tmp_path, roadmap_content=roadmap)
        # Single weak keyword — score=1
        r = run_hook("there is a bug in the authentication module somewhere", tmp_cwd=cwd,
                     session_id="test-idle-amb")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None
        assert "stage:" in ctx, f"State suffix must be present when ambiguous: {ctx!r}"


class TestMissingTrackIntents:
    """hotfix, chore, spike must be detectable from natural language."""

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

    def test_emergency_detects_hotfix(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("emergency fix needed for the production issue right now", tmp_cwd=cwd,
                     session_id="test-hf-emergency")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None, "Expected context for emergency message"
        assert "/hotfix" in ctx, f"Expected /hotfix suggestion, got: {ctx!r}"

    def test_explore_detects_spike(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("let us explore and investigate this approach first as a prototype", tmp_cwd=cwd,
                     session_id="test-spike-explore")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None, "Expected context for explore message"
        assert "/spike" in ctx, f"Expected /spike suggestion, got: {ctx!r}"

    def test_maintenance_detects_chore(self, tmp_path):
        cwd = make_cwd_with_zf(tmp_path)
        r = run_hook("housekeeping and maintenance tasks for the codebase cleanup", tmp_cwd=cwd,
                     session_id="test-chore-maint")
        ctx = self._parse_context(r.stdout)
        assert ctx is not None, "Expected context for maintenance message"
        assert "/chore" in ctx, f"Expected /chore suggestion, got: {ctx!r}"
