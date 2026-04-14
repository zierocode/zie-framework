"""Structural tests: reviewers use context_bundle from caller (ADR-054 inlined).

Reviewers receive context via context_bundle — no direct cache helper calls.
The load-context skill owns cache logic; reviewers are pure consumers.
"""
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def _skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def test_spec_reviewer_requires_context_bundle():
    """spec-reviewer receives context_bundle from caller."""
    text = _skill_text("spec-reviewer")
    assert "context_bundle" in text, "spec-reviewer must reference context_bundle"
    assert "Phase 1" in text and "Validate Context Bundle" in text


def test_plan_reviewer_requires_context_bundle():
    """plan-reviewer receives context_bundle from caller."""
    text = _skill_text("plan-reviewer")
    assert "context_bundle" in text, "plan-reviewer must reference context_bundle"
    assert "Phase 1" in text and "Validate Context Bundle" in text


def test_impl_reviewer_requires_context_bundle():
    """impl-reviewer receives context_bundle from caller."""
    text = _skill_text("impl-reviewer")
    assert "context_bundle" in text, "impl-reviewer must reference context_bundle"
    assert "Phase 1" in text and "Validate Context Bundle" in text


def test_load_context_owns_cache_logic():
    """load-context skill owns ADR cache logic (unified CacheManager)."""
    text = _skill_text("load-context")
    assert "get_cache_manager" in text or "get_or_compute" in text, \
        "load-context must reference unified cache API"
    assert "cache" in text.lower(), \
        "load-context must reference caching"


def test_load_context_has_cache_miss_fallback():
    text = _skill_text("load-context")
    assert "Cache miss" in text or "cache miss" in text or "Cache miss:" in text


def test_load_context_has_cache_hit_skip():
    text = _skill_text("load-context")
    assert "Cache hit" in text or "cache hit" in text or "Cache hit:" in text
