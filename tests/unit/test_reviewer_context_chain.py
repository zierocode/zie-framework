"""Structural tests for lean-reviewer-context-chain-depth.

Reviewers must inline their context load (fast-path + disk-fallback) rather than
calling Skill(reviewer-context), reducing hop depth from 3-4 to 1-2.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


import pytest


@pytest.mark.parametrize("skill", ["spec-reviewer", "plan-reviewer", "impl-reviewer"])
def test_reviewer_disk_fallback_summary_before_wildcard(skill):
    """Reviewer Phase 1 disk fallback must load ADR-000-summary.md before any wildcard load."""
    text = _read(f"skills/{skill}/SKILL.md")
    assert "ADR-000-summary.md" in text, (
        f"skills/{skill}/SKILL.md must reference ADR-000-summary.md"
    )
    adr_summary_pos = text.index("ADR-000-summary.md")
    wildcard_pos = text.index("decisions/*.md") if "decisions/*.md" in text else len(text)
    assert adr_summary_pos < wildcard_pos, (
        f"skills/{skill}/SKILL.md: ADR-000-summary.md must appear before decisions/*.md wildcard"
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
    """Phase 1 must have Fast-path, Disk fallback, Returns in order."""
    phase1 = _extract_phase1("skills/spec-reviewer/SKILL.md")
    assert "**Fast-path:**" in phase1, "spec-reviewer Phase 1 missing Fast-path bullet"
    assert "**Disk fallback:**" in phase1, "spec-reviewer Phase 1 missing Disk fallback bullet"
    assert "Returns:" in phase1, "spec-reviewer Phase 1 missing Returns line"
    assert phase1.find("Fast-path") < phase1.find("Disk fallback") < phase1.find("Returns"), \
        "spec-reviewer Phase 1 bullets out of order"


def test_plan_reviewer_phase1_structure():
    """Phase 1 must have Fast-path, Disk fallback, Returns in order."""
    phase1 = _extract_phase1("skills/plan-reviewer/SKILL.md")
    assert "**Fast-path:**" in phase1, "plan-reviewer Phase 1 missing Fast-path bullet"
    assert "**Disk fallback:**" in phase1, "plan-reviewer Phase 1 missing Disk fallback bullet"
    assert "Returns:" in phase1, "plan-reviewer Phase 1 missing Returns line"
    assert phase1.find("Fast-path") < phase1.find("Disk fallback") < phase1.find("Returns"), \
        "plan-reviewer Phase 1 bullets out of order"


def test_impl_reviewer_phase1_structure():
    """Phase 1 must have Fast-path, Disk fallback, Returns in order."""
    phase1 = _extract_phase1("skills/impl-reviewer/SKILL.md")
    assert "**Fast-path:**" in phase1, "impl-reviewer Phase 1 missing Fast-path bullet"
    assert "**Disk fallback:**" in phase1, "impl-reviewer Phase 1 missing Disk fallback bullet"
    assert "Returns:" in phase1, "impl-reviewer Phase 1 missing Returns line"
    assert phase1.find("Fast-path") < phase1.find("Disk fallback") < phase1.find("Returns"), \
        "impl-reviewer Phase 1 bullets out of order"


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
