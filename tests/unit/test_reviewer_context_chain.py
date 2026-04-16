"""Structural tests for merged reviewer and context skills.

The review skill handles all 3 phases (spec/plan/impl) via parameter.
The context skill handles both ADR loading and framework reference maps.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text()


import pytest


def test_review_skill_requires_context_bundle():
    """Review skill must require context_bundle from caller."""
    text = _read("skills/review/SKILL.md")
    assert "context_bundle" in text, "review must reference context_bundle"
    assert "Phase 1" in text and "Validate Context Bundle" in text


def test_review_skill_has_phase_parameter():
    """Review skill must support phase=spec|plan|impl parameter."""
    text = _read("skills/review/SKILL.md")
    assert "phase=spec" in text, "review must support phase=spec"
    assert "phase=plan" in text, "review must support phase=plan"
    assert "phase=impl" in text, "review must support phase=impl"


def test_review_skill_no_reviewer_context_call():
    """Review skill must NOT invoke Skill(reviewer-context) — uses inline context load."""
    text = _read("skills/review/SKILL.md")
    assert "Skill(reviewer-context)" not in text, (
        "review must use context_bundle passthrough, not call Skill(reviewer-context)"
    )


def test_review_skill_has_inline_fast_path():
    """Review Phase 1 must have context_bundle fast-path."""
    text = _read("skills/review/SKILL.md")
    assert "context_bundle" in text and (
        "fast" in text.lower() or "fast-path" in text.lower() or "disk" in text.lower()
    ), "review must have inline fast-path context load"


def test_review_skill_phase1_structure():
    """Phase 1 must have context_bundle validation with Returns statement."""
    phase1_start = text = _read("skills/review/SKILL.md")
    idx = text.find("## Phase 1")
    assert idx >= 0, "review must have Phase 1 section"
    phase1 = text[idx:text.find("## Phase 2", idx)]
    assert "context_bundle" in phase1, "review Phase 1 missing context_bundle reference"
    assert "Returns:" in phase1, "review Phase 1 missing Returns line"


def test_spec_design_passes_context_bundle_to_reviewer():
    """spec-design must pass context_bundle when invoking review."""
    text = _read("skills/spec-design/SKILL.md")
    assert "context_bundle" in text, "spec-design must pass context_bundle to Skill(zie-framework:review)"


def test_write_plan_passes_context_bundle_to_reviewer():
    """commands/plan.md must pass context_bundle when invoking review."""
    text = _read("commands/plan.md")
    assert "context_bundle" in text, "commands/plan.md must pass context_bundle to Skill(zie-framework:review)"


def test_project_md_no_reviewer_context_row():
    """PROJECT.md Skills table must not list reviewer-context after deletion."""
    text = (REPO_ROOT / "zie-framework" / "PROJECT.md").read_text()
    start = text.find("## Skills") if "## Skills" in text else 0
    end = text.find("\n## ", start + 1) if "\n## " in text[start + 1 :] else len(text)
    skills_section = text[start:end]
    assert "reviewer-context" not in skills_section, (
        "PROJECT.md Skills table still lists reviewer-context — should be removed"
    )


def test_reviewer_context_skill_deleted():
    """reviewer-context skill must be deleted — it is dead code (ADR-054)."""
    skill_path = REPO_ROOT / "skills" / "reviewer-context" / "SKILL.md"
    assert not skill_path.exists(), "skills/reviewer-context/SKILL.md still exists — delete it (ADR-054)"


def test_old_reviewer_skills_deleted():
    """Old separate reviewer skills must be deleted — merged into review skill."""
    for name in ["spec-review", "plan-review", "impl-review"]:
        skill_path = REPO_ROOT / "skills" / name / "SKILL.md"
        assert not skill_path.exists(), f"skills/{name}/SKILL.md still exists — merged into skills/review"


def test_old_context_skills_deleted():
    """Old separate context skills must be deleted — merged into context skill."""
    for name in ["context-map", "load-context"]:
        skill_path = REPO_ROOT / "skills" / name / "SKILL.md"
        assert not skill_path.exists(), f"skills/{name}/SKILL.md still exists — merged into skills/context"