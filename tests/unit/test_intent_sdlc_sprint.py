"""Tests for sprint intent detection in intent-sdlc hook.

Uses text + AST parsing since intent-sdlc.py calls sys.exit() at module level
(via read_event()) and cannot be directly imported.
"""
import ast
import re
from pathlib import Path

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


class TestSprintPatternsInSource:
    def test_sprint_key_in_patterns(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        assert "sprint" in patterns, \
            "PATTERNS must have 'sprint' key"

    def test_sprint_suggestion(self):
        suggestions = _extract_dict_literal(_source(), "SUGGESTIONS")
        assert suggestions.get("sprint") == "/zie-sprint", \
            "SUGGESTIONS['sprint'] must be '/zie-sprint'"

    def test_sprint_patterns_not_empty(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        assert len(patterns.get("sprint", [])) > 0, \
            "sprint PATTERNS list must not be empty"


class TestSprintRegexMatching:
    """Extract sprint patterns from source and verify regex behavior."""

    def _sprint_compiled(self):
        patterns = _extract_dict_literal(_source(), "PATTERNS")
        return [re.compile(p) for p in patterns.get("sprint", [])]

    def test_english_sprint_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("sprint") for p in compiled), \
            "must match English 'sprint'"

    def test_clear_backlog_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("clear backlog") for p in compiled), \
            "must match 'clear backlog'"

    def test_thai_clear_backlog_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("เคลียร์ backlog") for p in compiled), \
            "must match Thai 'เคลียร์ backlog'"

    def test_ship_all_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("ship all") for p in compiled), \
            "must match 'ship all'"

    def test_zie_sprint_pattern(self):
        compiled = self._sprint_compiled()
        assert any(p.search("zie-sprint") for p in compiled), \
            "must match 'zie-sprint'"
