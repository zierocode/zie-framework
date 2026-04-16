"""Structural tests for merged context skill.

Verifies fast-path wording exists in the context skill file so downstream
commands can skip redundant disk reads when context_bundle is already loaded.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


def test_context_skill_has_context_bundle_fast_path():
    """context skill must return immediately if context_bundle provided."""
    text = _read("skills/context/SKILL.md")
    assert "context_bundle" in text, "skills/context/SKILL.md must reference context_bundle"
    # Fast path: return immediately when bundle provided
    assert "return" in text.lower() or "skip" in text.lower(), (
        "skills/context/SKILL.md must document fast-path return"
    )


def test_context_skill_fast_path_documented():
    """context SKILL.md must have a fast-path guard for context_bundle."""
    text = _read("skills/context/SKILL.md")
    assert "context_bundle" in text and "return" in text.lower(), (
        "skills/context/SKILL.md must document fast-path: if context_bundle provided → return immediately"
    )


def test_sprint_passes_context_bundle_to_implement():
    """sprint.md Phase 3 must pass context_bundle to implement."""
    text = _read("commands/sprint.md")
    assert "context_bundle" in text, "commands/sprint.md must pass context_bundle in Phase 3"


def test_implement_passes_context_bundle_to_reviewer():
    """implement.md must pass context_bundle to review skill."""
    text = _read("commands/implement.md")
    assert "context_bundle" in text, "commands/implement.md must pass context_bundle to review"