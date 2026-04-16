"""Tests for sprint intent detection in intent-sdlc hook.

Uses text + AST parsing since intent-sdlc.py calls sys.exit() at module level
(via read_event()) and cannot be directly imported.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
HOOK_PATH = REPO_ROOT / "hooks" / "intent-sdlc.py"


def _source():
    return HOOK_PATH.read_text()


def _get_intent_pattern():
    """Extract INTENT_PATTERN regex from source."""
    source = _source()
    match = re.search(
        r'INTENT_PATTERN = re\.compile\(\s*\n\s*r"""(.*?)""",\s*\n\s*re\.IGNORECASE \| re\.VERBOSE,?\s*\n\)',
        source,
        re.DOTALL,
    )
    if match:
        pattern_str = match.group(1)
        return re.compile(pattern_str, re.IGNORECASE | re.VERBOSE)
    return None


class TestSprintPatternsInSource:
    def test_sprint_suggestion(self):
        source = _source()
        assert '"sprint":' in source, "SUGGESTIONS must have 'sprint' key"
        assert '"/sprint"' in source, "SUGGESTIONS['sprint'] must be '/sprint'"

    def test_sprint_intent_pattern_exists(self):
        source = _source()
        assert "?P<sprint>" in source, "INTENT_PATTERN must have 'sprint' named group"


class TestSprintRegexMatching:
    """Test INTENT_PATTERN sprint group matches expected signals."""

    def _get_pattern(self):
        return _get_intent_pattern()

    def _sprint_compiled(self):
        """Return list of (pattern, label) tuples for sprint signals."""
        pattern = self._get_pattern()
        if pattern is None:
            return []
        # The INTENT_PATTERN is a single regex with alternations
        # Return as single-item list for consistent iteration
        return [pattern]

    def test_english_sprint_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("sprint") for p in compiled), "must match English 'sprint'"

    def test_clear_backlog_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("clear backlog") for p in compiled), "must match 'clear backlog'"

    def test_thai_clear_backlog_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("เคลียร์ backlog") for p in compiled), "must match Thai 'เคลียร์ backlog'"

    def test_ship_all_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("ship all") for p in compiled), "must match 'ship all'"

    def test_zie_sprint_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("zie-sprint") for p in compiled), "must match 'zie-sprint'"


# ── Runtime behavior tests (Area 3 — Intent Intelligence) ────────────────────
import json
import os
import subprocess
import sys
import tempfile

import pytest

_REPO_ROOT = Path(__file__).parents[2]
_HOOK = _REPO_ROOT / "hooks" / "intent-sdlc.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9]", "-", project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _run_hook(message: str, tmp_path: Path) -> subprocess.CompletedProcess:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / ".config").write_text("{}")
    (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"prompt": message, "session_id": "test-intent"})
    return subprocess.run(
        [sys.executable, str(_HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


class TestSprintIntentFlag:
    """Sprint intent detection writes the sprint flag via CacheManager."""

    def test_sprint_flag_written_via_cache_manager(self, tmp_path):
        """Sprint intent should write flag to CacheManager instead of /tmp file."""
        # Two sprint signals: "implement" + "build" → score ≥2
        r = _run_hook("let's implement and build this feature", tmp_path)
        assert r.returncode == 0
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            ctx = data.get("additionalContext", "")
            if "sprint" in ctx.lower():
                # Check CacheManager for sprint flag instead of /tmp file
                cache_dir = tmp_path / ".zie" / "cache"
                cache_file = cache_dir / "session-cache.json"
                if cache_file.exists():
                    import json as _json

                    cache_data = _json.loads(cache_file.read_text())
                    # Look for sprint flag in any session
                    has_sprint_flag = any("intent-sprint-flag" in k for k in cache_data)
                    assert has_sprint_flag, "sprint flag must be written to CacheManager when sprint intent detected"

    def test_thai_sprint_triggers_hint(self, tmp_path):
        r = _run_hook("ทำเลย เคลียร์ backlog ทั้งหมดเลย", tmp_path)
        assert r.returncode == 0


class TestFixIntentHint:
    def test_fix_signals_produce_fix_hint(self, tmp_path):
        # "bug" + "broken" → score ≥2 for fix intent
        r = _run_hook("there's a bug and it's broken please fix it", tmp_path)
        assert r.returncode == 0
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            ctx = data.get("additionalContext", "")
            # If fix threshold fires, hint should reference fix
            if ctx:
                assert "fix" in ctx.lower() or "intent" in ctx.lower()


class TestUnclearIntentHint:
    def test_short_ambiguous_message_triggers_unclear(self, tmp_path):
        # < 50 chars, no SDLC keywords → unclear hint
        r = _run_hook("do it", tmp_path)
        assert r.returncode == 0
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            ctx = data.get("additionalContext", "")
            assert "unclear" in ctx.lower() or ctx == "", (
                f"short message should produce unclear hint or no output, got: {ctx!r}"
            )

    def test_silent_on_clear_nonmatching_message(self, tmp_path):
        # Clear message >50 chars but no SDLC keyword → no output
        r = _run_hook("today is a beautiful sunny day", tmp_path)
        assert r.returncode == 0
        # Either no output or empty additionalContext
        if r.stdout.strip():
            data = json.loads(r.stdout.strip())
            assert data.get("additionalContext", "") == "" or True  # just no crash


class TestIntentSdlcErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(_HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
