"""
Test that Phase 1 of each reviewer skill is a compact delegation stub.

After consolidation, the Phase 1 block should delegate to reviewer-context
rather than duplicating the disk-fallback logic inline.
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def _phase1_lines(skill_name: str) -> int:
    """Count lines in Phase 1 section of a reviewer skill."""
    text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
    lines = text.splitlines()
    in_phase1 = False
    count = 0
    for line in lines:
        if "## Phase 1" in line:
            in_phase1 = True
            continue
        if in_phase1 and line.startswith("## "):
            break
        if in_phase1:
            count += 1
    return count


def test_spec_reviewer_phase1_is_compact():
    """Phase 1 must be a compact stub — no inline ADR read prose."""
    assert _phase1_lines("spec-review") <= 8, "spec-review Phase 1 is too long — inline disk-fallback prose not removed"


def test_plan_reviewer_phase1_is_compact():
    """Phase 1 must be a compact stub — no inline ADR read prose."""
    assert _phase1_lines("plan-review") <= 8, "plan-review Phase 1 is too long — inline disk-fallback prose not removed"


def test_impl_reviewer_phase1_is_compact():
    """Phase 1 must be a compact stub — no inline ADR read steps.
    12-line limit allows for adr_cache_path note and 'files changed' step.
    """
    assert _phase1_lines("impl-review") <= 12, (
        "impl-review Phase 1 is too long — inline disk-fallback prose not removed"
    )
