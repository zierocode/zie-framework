"""Structural tests for context-bundle reviewer pattern.

Reviewers receive context via context_bundle from caller (not disk reads).
Phase 1 validates bundle presence and documents fallback behavior.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


import pytest


@pytest.mark.parametrize("skill", ["spec-reviewer", "plan-reviewer", "impl-reviewer"])
def test_reviewer_requires_context_bundle(skill):
    """Reviewer Phase 1 must require context_bundle from caller."""
    text = _read(f"skills/{skill}/SKILL.md")
    assert "context_bundle" in text, (
        f"skills/{skill}/SKILL.md must reference context_bundle"
    )
    # Verify Phase 1 has validation
    assert "Phase 1" in text and "Validate Context Bundle" in text, (
        f"skills/{skill}/SKILL.md missing Phase 1 context bundle validation"
    )


def test_spec_reviewer_no_skill_reviewer_context_call():
    """spec-reviewer must NOT invoke Skill(reviewer-context) — use inline context load."""
    text = _read("skills/spec-reviewer/SKILL.md")
    assert "Skill(reviewer-context)" not in text, (
        "spec-reviewer must inline context load, not call Skill(reviewer-context)"
    )


def test_plan_reviewer_no_skill_reviewer_context_call():
    """plan-reviewer must NOT invoke Skill(reviewer-context) — use inline context load."""
    text = _read("skills/plan-reviewer/SKILL.md")
    assert "Skill(reviewer-context)" not in text, (
        "plan-reviewer must inline context load, not call Skill(reviewer-context)"
    )


def test_impl_reviewer_no_skill_reviewer_context_call():
    """impl-reviewer must NOT invoke Skill(reviewer-context) — use inline context load."""
    text = _read("skills/impl-reviewer/SKILL.md")
    assert "Skill(reviewer-context)" not in text, (
        "impl-reviewer must inline context load, not call Skill(reviewer-context)"
    )


def test_spec_reviewer_has_inline_fast_path():
    """spec-reviewer Phase 1 must have context_bundle fast-path inline."""
    text = _read("skills/spec-reviewer/SKILL.md")
    assert "context_bundle" in text and ("fast" in text.lower() or "fast-path" in text.lower() or "disk" in text.lower()), (
        "spec-reviewer must have inline fast-path context load"
    )


def test_plan_reviewer_has_inline_fast_path():
    """plan-reviewer Phase 1 must have context_bundle fast-path inline."""
    text = _read("skills/plan-reviewer/SKILL.md")
    assert "context_bundle" in text and ("fast" in text.lower() or "disk" in text.lower()), (
        "plan-reviewer must have inline fast-path context load"
    )


def test_impl_reviewer_has_inline_fast_path():
    """impl-reviewer Phase 1 must have context_bundle fast-path inline."""
    text = _read("skills/impl-reviewer/SKILL.md")
    assert "context_bundle" in text and ("fast" in text.lower() or "disk" in text.lower()), (
        "impl-reviewer must have inline fast-path context load"
    )


def test_spec_design_passes_context_bundle_to_reviewer():
    """spec-design must pass context_bundle when invoking spec-reviewer."""
    text = _read("skills/spec-design/SKILL.md")
    assert "context_bundle" in text, (
        "spec-design must pass context_bundle to Skill(zie-framework:spec-reviewer)"
    )


def test_write_plan_passes_context_bundle_to_reviewer():
    """commands/plan.md must pass context_bundle when invoking plan-reviewer."""
    text = _read("commands/plan.md")
    assert "context_bundle" in text, (
        "commands/plan.md must pass context_bundle to Skill(zie-framework:plan-reviewer)"
    )


def _extract_phase1(skill_path: str) -> str:
    text = (REPO_ROOT / skill_path).read_text()
    start = text.find("## Phase 1")
    end = text.find("## Phase 2", start)
    return text[start:end]


def test_spec_reviewer_phase1_structure():
    """Phase 1 must have context_bundle validation with Returns statement."""
    phase1 = _extract_phase1("skills/spec-reviewer/SKILL.md")
    assert "context_bundle" in phase1, "spec-reviewer Phase 1 missing context_bundle reference"
    assert "Returns:" in phase1, "spec-reviewer Phase 1 missing Returns line"


def test_plan_reviewer_phase1_structure():
    """Phase 1 must have context_bundle validation with Returns statement."""
    phase1 = _extract_phase1("skills/plan-reviewer/SKILL.md")
    assert "context_bundle" in phase1, "plan-reviewer Phase 1 missing context_bundle reference"
    assert "Returns:" in phase1, "plan-reviewer Phase 1 missing Returns line"


def test_impl_reviewer_phase1_structure():
    """Phase 1 must have context_bundle validation with Returns statement."""
    phase1 = _extract_phase1("skills/impl-reviewer/SKILL.md")
    assert "context_bundle" in phase1, "impl-reviewer Phase 1 missing context_bundle reference"
    assert "Returns:" in phase1, "impl-reviewer Phase 1 missing Returns line"


def test_project_md_no_reviewer_context_row():
    """PROJECT.md Skills table must not list reviewer-context after deletion."""
    text = (REPO_ROOT / "zie-framework" / "PROJECT.md").read_text()
    start = text.find("## Skills") if "## Skills" in text else 0
    end = text.find("\n## ", start + 1) if "\n## " in text[start + 1:] else len(text)
    skills_section = text[start:end]
    assert "reviewer-context" not in skills_section, (
        "PROJECT.md Skills table still lists reviewer-context — should be removed"
    )


def test_reviewer_context_skill_deleted():
    """reviewer-context skill must be deleted — it is dead code (ADR-054)."""
    skill_path = REPO_ROOT / "skills" / "reviewer-context" / "SKILL.md"
    assert not skill_path.exists(), (
        "skills/reviewer-context/SKILL.md still exists — delete it (ADR-054)"
    )
