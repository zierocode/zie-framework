"""Regression tests for module-level pattern compilation in intent-sdlc.py."""
import ast
from pathlib import Path

HOOK_PATH = Path(__file__).parents[2] / "hooks" / "intent-sdlc.py"


def _get_module_level_names(tree: ast.Module) -> set:
    names = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _has_compile_inside_function(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    func = child.func
                    if isinstance(func, ast.Attribute) and func.attr == "compile":
                        return True
                    if isinstance(func, ast.Name) and func.id == "compile":
                        return True
    return False


def test_hotfix_pattern_in_patterns():
    """NEW_INTENT_REGEXES must include 'hotfix' or intent-sdlc must handle hotfix."""
    text = HOOK_PATH.read_text()
    # hotfix is handled via INTENT_PATTERN regex with ?P<hotfix> named group
    assert "?P<hotfix>" in text or '"hotfix"' in text, (
        "intent-sdlc.py must include 'hotfix' pattern"
    )


def test_chore_pattern_in_patterns():
    """NEW_INTENT_REGEXES must include 'chore' category."""
    text = HOOK_PATH.read_text()
    assert '"chore"' in text or "'chore'" in text or "?P<chore>" in text, (
        "intent-sdlc.py must include 'chore' pattern"
    )


def test_spike_pattern_in_patterns():
    """INTENT_PATTERN must include 'spike' category."""
    text = HOOK_PATH.read_text()
    assert "?P<spike>" in text, (
        "intent-sdlc.py INTENT_PATTERN must include 'spike' named group"
    )


def test_new_intent_patterns_at_module_level():
    """NEW_INTENT_PATTERNS must be a module-level dict (replaces NEW_INTENT_REGEXES)."""
    source = HOOK_PATH.read_text()
    tree = ast.parse(source)
    module_names = _get_module_level_names(tree)
    assert "NEW_INTENT_PATTERNS" in module_names, (
        "NEW_INTENT_PATTERNS must be defined at module level, not inside a function"
    )


def test_no_re_compile_inside_functions():
    """re.compile must not be called inside any function (patterns compiled at module level)."""
    source = HOOK_PATH.read_text()
    tree = ast.parse(source)
    assert not _has_compile_inside_function(tree), (
        "re.compile() found inside a function — move pattern compilation to module level"
    )
