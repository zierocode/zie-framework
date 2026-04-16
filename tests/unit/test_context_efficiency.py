"""Unit tests for context efficiency improvements (Area 2)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
from utils_cache import CacheManager

REPO_ROOT = Path(__file__).parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"

# ── FAST PATH token budget ────────────────────────────────────────────────────
# Rough token estimate: 1 token ≈ 4 chars for English prose.
# These thresholds are generous to avoid false failures from minor content edits.
FAST_PATH_BUDGETS = {
    "review": 600,  # ≤120 tokens ≈ 480 chars; 600 gives 25% margin
    "context": 300,  # ≤60 tokens ≈ 240 chars; 300 gives 25% margin
}


class TestFastPathPresent:
    """FAST PATH block exists in each qualifying skill file."""

    def _fast_path_block(self, skill_name: str) -> str:
        path = REPO_ROOT / "skills" / skill_name / "SKILL.md"
        assert path.exists(), f"skills/{skill_name}/SKILL.md must exist"
        content = path.read_text()
        marker = "<!-- FAST PATH -->"
        assert marker in content, f"skills/{skill_name}/SKILL.md must contain '<!-- FAST PATH -->' marker"
        # Extract text between FAST PATH and DETAIL markers
        parts = content.split(marker, 1)
        if len(parts) < 2:
            return ""
        detail_marker = "<!-- DETAIL"
        fast_section = parts[1].split(detail_marker, 1)[0]
        return fast_section

    def test_review_has_fast_path(self):
        block = self._fast_path_block("review")
        assert len(block) > 0

    def test_context_has_fast_path(self):
        block = self._fast_path_block("context")
        assert len(block) > 0

    def test_review_fast_path_under_budget(self):
        block = self._fast_path_block("review")
        assert len(block) <= FAST_PATH_BUDGETS["review"], (
            f"review FAST PATH is {len(block)} chars, must be ≤{FAST_PATH_BUDGETS['review']}"
        )

    def test_context_fast_path_under_budget(self):
        block = self._fast_path_block("context")
        assert len(block) <= FAST_PATH_BUDGETS["context"], (
            f"context FAST PATH is {len(block)} chars, must be ≤{FAST_PATH_BUDGETS['context']}"
        )


# ── subagent-context cache tests ──────────────────────────────────────────────

HOOK = HOOKS_DIR / "subagent-context.py"

SESSION_ID = "test-session"


def _make_zf(tmp_path: Path) -> None:
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    (zf / ".config").write_text('{"project_type": "lib"}')
    (zf / "ROADMAP.md").write_text("## Now\n\n- active-feature\n\n## Next\n\n## Done\n")


def _run_hook(tmp_path: Path, agent_type: str, session_id: str = SESSION_ID) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"agentType": agent_type, "session_id": session_id})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


class TestSubagentContextCache:
    def test_injects_on_cache_miss(self, tmp_path):
        _make_zf(tmp_path)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        out = r.stdout.strip()
        assert out, "should emit additionalContext on cache miss"

    def test_writes_cache_flag_on_inject(self, tmp_path):
        _make_zf(tmp_path)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        # Verify cache flag written via CacheManager (unified session cache)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        assert cache.has_flag("session-context-injected", SESSION_ID), "cache flag must be written after first inject"

    def test_skips_inject_on_cache_hit(self, tmp_path):
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.set_flag("session-context-injected", SESSION_ID)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        # On cache hit the hook exits 0 with no stdout
        assert r.stdout.strip() == "", "should emit nothing on cache hit"


class TestSubagentContextBudgetTable:
    """Per-agent budget table routes the right context to each agent type."""

    def test_explore_agent_gets_context(self, tmp_path):
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.delete("session-context-injected", SESSION_ID)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        assert r.stdout.strip(), "Explore agent must receive context"

    def test_brainstorm_agent_gets_no_context(self, tmp_path):
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.delete("session-context-injected", SESSION_ID)
        r = _run_hook(tmp_path, "brainstorm")
        assert r.returncode == 0
        assert r.stdout.strip() == "", "brainstorm agent must receive NO context injection"

    def test_unknown_agent_falls_back_to_conservative_default(self, tmp_path):
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.delete("session-context-injected", SESSION_ID)
        r = _run_hook(tmp_path, "UnknownAgentType42")
        # Unknown gets conservative default — exits 0, may or may not emit
        assert r.returncode == 0

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0


class TestSessionCleanup:
    """session-cleanup.py clears session-context cache via CacheManager."""

    def test_cleanup_clears_context_flag(self, tmp_path):
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.set_flag("session-context-injected", "test-session")
        assert cache.has_flag("session-context-injected", "test-session")

        cleanup_hook = HOOKS_DIR / "session-cleanup.py"
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(cleanup_hook)],
            input=json.dumps({"session_id": "test-session", "stop_reason": "end_turn"}),
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        # Use a fresh CacheManager to verify disk state (in-memory cache won't
        # reflect subprocess changes)
        fresh_cache = CacheManager(tmp_path / ".zie" / "cache")
        assert not fresh_cache.has_flag("session-context-injected", "test-session"), (
            "session-cleanup must clear the session-context cache flag"
        )

    def test_cleanup_handles_missing_flag_gracefully(self, tmp_path):
        _make_zf(tmp_path)
        cache = CacheManager(tmp_path / ".zie" / "cache")
        cache.delete("session-context-injected", "test-session")

        cleanup_hook = HOOKS_DIR / "session-cleanup.py"
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(cleanup_hook)],
            input=json.dumps({"session_id": "test-session", "stop_reason": "end_turn"}),
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0  # no exception when flag is already absent
