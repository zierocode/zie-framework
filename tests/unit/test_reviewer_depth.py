from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SKILLS = ROOT / "skills"


def read_skill(name):
    return (SKILLS / name / "SKILL.md").read_text()


# ── spec-reviewer ────────────────────────────────────────────────────────────

def test_spec_reviewer_has_context_bundle():
    content = read_skill("spec-reviewer")
    assert "context_bundle" in content, (
        "spec-reviewer must reference context_bundle"
    )


def test_spec_reviewer_phase1_validates_bundle():
    content = read_skill("spec-reviewer")
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        "spec-reviewer must have Phase 1 context bundle validation"
    )


def test_spec_reviewer_has_disk_fallback():
    content = read_skill("spec-reviewer")
    # Must have disk fallback documented when bundle unavailable
    assert "decisions/" in content or "disk" in content.lower(), (
        "spec-reviewer must document disk fallback path"
    )


# ── plan-reviewer ────────────────────────────────────────────────────────────

def test_plan_reviewer_has_context_bundle():
    content = read_skill("plan-reviewer")
    assert "context_bundle" in content, (
        "plan-reviewer must reference context_bundle"
    )


def test_plan_reviewer_phase1_validates_bundle():
    content = read_skill("plan-reviewer")
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        "plan-reviewer must have Phase 1 context bundle validation"
    )


def test_plan_reviewer_has_disk_fallback():
    content = read_skill("plan-reviewer")
    assert "decisions/" in content or "disk" in content.lower(), (
        "plan-reviewer must document disk fallback path"
    )


def test_plan_reviewer_checks_pattern_match():
    content = read_skill("plan-reviewer")
    assert "pattern" in content.lower()


# ── impl-reviewer ────────────────────────────────────────────────────────────

def test_impl_reviewer_has_context_bundle():
    content = read_skill("impl-reviewer")
    assert "context_bundle" in content, (
        "impl-reviewer must reference context_bundle"
    )


def test_impl_reviewer_phase1_validates_bundle():
    content = read_skill("impl-reviewer")
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        "impl-reviewer must have Phase 1 context bundle validation"
    )


def test_impl_reviewer_no_roadmap_conflict_check():
    content = read_skill("impl-reviewer")
    assert "ROADMAP conflict" not in content


def test_impl_reviewer_checks_pattern_match():
    content = read_skill("impl-reviewer")
    assert "pattern" in content.lower()
