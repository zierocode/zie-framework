"""Regression tests for module-level COMPILED_PATTERNS in intent-sdlc.py."""
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
    """PATTERNS must include 'hotfix' category."""
    text = HOOK_PATH.read_text()
    assert '"hotfix"' in text or "'hotfix'" in text, (
        "intent-sdlc.py PATTERNS must include 'hotfix' category"
    )


def test_chore_pattern_in_patterns():
    """PATTERNS must include 'chore' category."""
    text = HOOK_PATH.read_text()
    assert '"chore"' in text or "'chore'" in text, (
        "intent-sdlc.py PATTERNS must include 'chore' category"
    )


def test_spike_pattern_in_patterns():
    """PATTERNS must include 'spike' category."""
    text = HOOK_PATH.read_text()
    assert '"spike"' in text or "'spike'" in text, (
        "intent-sdlc.py PATTERNS must include 'spike' category"
    )


def test_compiled_patterns_at_module_level():
    """COMPILED_PATTERNS must be a module-level assignment."""
    source = HOOK_PATH.read_text()
    tree = ast.parse(source)
    module_names = _get_module_level_names(tree)
    assert "COMPILED_PATTERNS" in module_names, (
        "COMPILED_PATTERNS must be defined at module level, not inside a function"
    )


def test_no_re_compile_inside_functions():
    """re.compile must not be called inside any function."""
    source = HOOK_PATH.read_text()
    tree = ast.parse(source)
    assert not _has_compile_inside_function(tree), (
        "re.compile() found inside a function — move pattern compilation to module level"
    )
