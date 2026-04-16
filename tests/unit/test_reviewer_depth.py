"""Depth tests for the consolidated review skill (merged from spec-review, plan-review, impl-review)."""

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SKILLS = ROOT / "skills"


def read_review():
    return (SKILLS / "review" / "SKILL.md").read_text()


# ── context_bundle ─────────────────────────────────────────────────────────


def test_review_has_context_bundle():
    content = read_review()
    assert "context_bundle" in content, "review must reference context_bundle"


def test_review_phase1_validates_bundle():
    content = read_review()
    assert "Phase 1" in content, "review must have Phase 1"
    assert "context_bundle" in content, "review Phase 1 must validate context_bundle"


def test_review_has_phase_param():
    content = read_review()
    assert "phase" in content.lower(), "review must support phase parameter"


# ── checklist coverage ───────────────────────────────────────────────────────


def test_review_covers_spec_checklist():
    content = read_review()
    assert "spec" in content.lower(), "review must cover spec phase"


def test_review_covers_plan_checklist():
    content = read_review()
    assert "plan" in content.lower(), "review must cover plan phase"


def test_review_covers_impl_checklist():
    content = read_review()
    assert "impl" in content.lower(), "review must cover impl phase"


def test_review_checks_pattern_match():
    content = read_review()
    assert "pattern" in content.lower()