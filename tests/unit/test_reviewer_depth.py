from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SKILLS = ROOT / "skills"


def read_skill(name):
    return (SKILLS / name / "SKILL.md").read_text()


# ── spec-review ────────────────────────────────────────────────────────────

def test_spec_reviewer_has_context_bundle():
    content = read_skill("spec-review")
    assert "context_bundle" in content, (
        "spec-review must reference context_bundle"
    )


def test_spec_reviewer_phase1_validates_bundle():
    content = read_skill("spec-review")
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        "spec-review must have Phase 1 context bundle validation"
    )


def test_spec_reviewer_has_disk_fallback():
    content = read_skill("spec-review")
    # Must have disk fallback documented when bundle unavailable
    assert "decisions/" in content or "disk" in content.lower(), (
        "spec-review must document disk fallback path"
    )


# ── plan-review ────────────────────────────────────────────────────────────

def test_plan_reviewer_has_context_bundle():
    content = read_skill("plan-review")
    assert "context_bundle" in content, (
        "plan-review must reference context_bundle"
    )


def test_plan_reviewer_phase1_validates_bundle():
    content = read_skill("plan-review")
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        "plan-review must have Phase 1 context bundle validation"
    )


def test_plan_reviewer_has_disk_fallback():
    content = read_skill("plan-review")
    assert "decisions/" in content or "disk" in content.lower(), (
        "plan-review must document disk fallback path"
    )


def test_plan_reviewer_checks_pattern_match():
    content = read_skill("plan-review")
    assert "pattern" in content.lower()


# ── impl-review ────────────────────────────────────────────────────────────

def test_impl_reviewer_has_context_bundle():
    content = read_skill("impl-review")
    assert "context_bundle" in content, (
        "impl-review must reference context_bundle"
    )


def test_impl_reviewer_phase1_validates_bundle():
    content = read_skill("impl-review")
    assert "Phase 1" in content and "Validate Context Bundle" in content, (
        "impl-review must have Phase 1 context bundle validation"
    )


def test_impl_reviewer_no_roadmap_conflict_check():
    content = read_skill("impl-review")
    assert "ROADMAP conflict" not in content


def test_impl_reviewer_checks_pattern_match():
    content = read_skill("impl-review")
    assert "pattern" in content.lower()
