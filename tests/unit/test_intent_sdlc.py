"""Tests for brainstorm intent detection in intent-sdlc hook (Area 0)."""
import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK_PATH = REPO_ROOT / "hooks" / "intent-sdlc.py"


def _source():
    return HOOK_PATH.read_text()


def _extract_dict_literal(source: str, var_name: str) -> dict:
    """Extract a module-level dict assignment by variable name using AST."""
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    if isinstance(node.value, ast.Dict):
                        result = {}
                        for k, v in zip(node.value.keys, node.value.values):
                            if isinstance(k, ast.Constant):
                                if isinstance(v, ast.List):
                                    result[k.value] = [
                                        elt.value for elt in v.elts
                                        if isinstance(elt, ast.Constant)
                                    ]
                                elif isinstance(v, ast.Constant):
                                    result[k.value] = v.value
                        return result
    return {}


class TestBrainstormPatternInSource:
    def test_patterns_and_suggestions_are_dicts(self):
        """Guard: verify PATTERNS and SUGGESTIONS are extractable dicts before other tests run."""
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        suggestions = _extract_dict_literal(_source(), "SUGGESTIONS")
        assert isinstance(patterns, dict) and len(patterns) > 0, \
            "PATTERNS must be a non-empty dict extractable via AST"
        assert isinstance(suggestions, dict) and len(suggestions) > 0, \
            "SUGGESTIONS must be a non-empty dict extractable via AST"

    def test_brainstorm_key_in_patterns(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        assert "brainstorm" in patterns, "PATTERNS must have 'brainstorm' key"

    def test_brainstorm_suggestion_is_skill(self):
        suggestions = _extract_dict_literal(_source(), "SUGGESTIONS")
        hint = suggestions.get("brainstorm", "")
        assert "brainstorm" in hint.lower(), (
            f"SUGGESTIONS['brainstorm'] must reference brainstorm skill, got: {hint!r}"
        )

    def test_brainstorm_patterns_not_empty(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        assert len(patterns.get("brainstorm", [])) >= 4, (
            "brainstorm PATTERNS must have at least 4 signal strings"
        )


class TestBrainstormRegexMatching:
    """Extract brainstorm patterns and verify they match expected signals."""

    def _compiled(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        compiled = []
        for p in patterns.get("brainstorm", []):
            try:
                compiled.append(re.compile(p, re.IGNORECASE))
            except re.error as e:
                pytest.fail(f"Invalid brainstorm regex pattern {p!r}: {e}")
        return compiled

    def test_matches_english_improve(self):
        compiled = self._compiled()
        assert any(p.search("improve") for p in compiled), "must match 'improve'"

    def test_matches_english_what_if(self):
        compiled = self._compiled()
        assert any(p.search("what if we added caching") for p in compiled), \
            "must match 'what if'"

    def test_matches_english_research(self):
        compiled = self._compiled()
        assert any(p.search("research this area") for p in compiled), \
            "must match 'research'"

    def test_matches_thai_should_add(self):
        compiled = self._compiled()
        assert any(p.search("น่าจะเพิ่ม") for p in compiled), \
            "must match Thai 'น่าจะเพิ่ม'"

    def test_does_not_match_clear_task(self):
        compiled = self._compiled()
        brainstorm_hits = sum(1 for p in compiled if p.search("fix bug in login"))
        assert brainstorm_hits < 2, (
            f"'fix bug in login' matched {brainstorm_hits} brainstorm signals — should be <2"
        )
