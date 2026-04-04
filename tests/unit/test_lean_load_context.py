"""Structural tests for lean-load-context-triple-invoke.

Verifies fast-path wording exists in skill/command files so the sprint→implement
chain can skip redundant disk reads when context_bundle is already loaded.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


def test_load_context_reads_summary_first():
    """load-context must load ADR-000-summary.md and fall back to full load if missing."""
    text = _read("skills/load-context/SKILL.md")
    assert "ADR-000-summary.md" in text, (
        "skills/load-context/SKILL.md must reference ADR-000-summary.md"
    )
    # Summary load must appear before the wildcard fallback
    assert text.index("ADR-000-summary.md") < text.index("ADR-*.md"), (
        "ADR-000-summary.md load must appear before ADR-*.md wildcard fallback in load-context"
    )


def test_load_context_fallback_documented():
    """load-context must document fallback when ADR-000-summary.md is missing."""
    text = _read("skills/load-context/SKILL.md")
    assert "missing" in text.lower() or "fall back" in text.lower() or "fallback" in text.lower(), (
        "skills/load-context/SKILL.md must document fallback when ADR-000-summary.md is absent"
    )



def test_load_context_fast_path_documented():
    """load-context SKILL.md must have a fast-path guard for context_bundle."""
    text = _read("skills/load-context/SKILL.md")
    assert "context_bundle" in text and "return" in text.lower(), (
        "skills/load-context/SKILL.md must document fast-path: "
        "if context_bundle provided → return immediately"
    )



def test_sprint_passes_context_bundle_to_implement():
    """sprint.md Phase 3 must pass context_bundle to zie-implement."""
    text = _read("commands/sprint.md")
    assert "context_bundle" in text, (
        "commands/sprint.md must pass context_bundle to Skill(zie-implement) in Phase 3"
    )


def test_implement_passes_context_bundle_to_reviewer():
    """implement.md must pass context_bundle to impl-reviewer."""
    text = _read("commands/implement.md")
    assert "context_bundle" in text, (
        "commands/implement.md must pass context_bundle to impl-reviewer"
    )
