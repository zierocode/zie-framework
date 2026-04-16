"""Tests for brainstorm intent detection in intent-sdlc hook (Area 0)."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
HOOK_PATH = REPO_ROOT / "hooks" / "intent-sdlc.py"


def _source():
    return HOOK_PATH.read_text()


class TestBrainstormPatternInSource:
    def test_suggestions_is_dict(self):
        """Guard: verify SUGGESTIONS is extractable dict before other tests run."""
        source = _source()
        assert "SUGGESTIONS = {" in source, "SUGGESTIONS must be a dict"

    def test_brainstorm_suggestion_is_skill(self):
        source = _source()
        assert '"brainstorm":' in source, "SUGGESTIONS must have 'brainstorm' key"
        assert "brainstorm" in source.lower(), "SUGGESTIONS['brainstorm'] must reference brainstorm skill"

    def test_brainstorm_intent_pattern_exists(self):
        source = _source()
        assert "?P<brainstorm>" in source, "INTENT_PATTERN must have 'brainstorm' named group"


class TestBrainstormRegexMatching:
    """Test INTENT_PATTERN brainstorm group matches expected signals."""

    def _get_pattern(self):
        source = _source()
        # Extract INTENT_PATTERN regex string (handles both single-line and multi-line format)
        match = re.search(
            r'INTENT_PATTERN = re\.compile\(\s*\n\s*r"""(.*?)""",\s*\n\s*re\.IGNORECASE \| re\.VERBOSE,?\s*\n\)',
            source,
            re.DOTALL,
        )
        if match:
            pattern_str = match.group(1)
            return re.compile(pattern_str, re.IGNORECASE | re.VERBOSE)
        return None

    def test_matches_english_improve(self):
        pattern = self._get_pattern()
        assert pattern is not None, "INTENT_PATTERN must be extractable"
        m = pattern.search("improve")
        assert m and m.lastgroup == "brainstorm", "must match 'improve' as brainstorm"

    def test_matches_english_what_if(self):
        pattern = self._get_pattern()
        assert pattern is not None
        m = pattern.search("what if we added caching")
        assert m and m.lastgroup == "brainstorm", "must match 'what if' as brainstorm"

    def test_matches_english_deep_dive(self):
        pattern = self._get_pattern()
        assert pattern is not None
        m = pattern.search("deep dive into this")
        assert m and m.lastgroup == "brainstorm", "must match 'deep dive' as brainstorm"

    def test_matches_thai_should_add(self):
        pattern = self._get_pattern()
        assert pattern is not None
        m = pattern.search("น่าจะเพิ่ม")
        assert m and m.lastgroup == "brainstorm", "must match Thai 'น่าจะเพิ่ม' as brainstorm"

    def test_does_not_match_clear_task(self):
        pattern = self._get_pattern()
        assert pattern is not None
        m = pattern.search("fix bug in login")
        assert m is None or m.lastgroup != "brainstorm", "'fix bug in login' should not match brainstorm"
