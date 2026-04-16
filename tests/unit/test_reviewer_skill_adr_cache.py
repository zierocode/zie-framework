"""Structural tests: reviewers use context_bundle from caller (ADR-054 inlined).

Reviewers receive context via context_bundle — no direct cache helper calls.
The context skill owns cache logic; reviewers are pure consumers.
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def _skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def test_review_skill_requires_context_bundle():
    """review skill receives context_bundle from caller."""
    text = _skill_text("review")
    assert "context_bundle" in text, "review must reference context_bundle"
    assert "Phase 1" in text and "Validate Context Bundle" in text


def test_review_skill_has_phase_parameter():
    """review skill supports phase=spec|plan|impl parameter."""
    text = _skill_text("review")
    assert "phase=spec" in text, "review must support phase=spec"
    assert "phase=plan" in text, "review must support phase=plan"
    assert "phase=impl" in text, "review must support phase=impl"


def test_context_skill_owns_cache_logic():
    """context skill owns ADR cache logic (unified CacheManager)."""
    text = _skill_text("context")
    assert "get_cache_manager" in text or "get_or_compute" in text, "context must reference unified cache API"
    assert "cache" in text.lower(), "context must reference caching"


def test_context_skill_has_cache_miss_fallback():
    text = _skill_text("context")
    assert "Cache hit" in text or "cache hit" in text or "Miss" in text or "miss" in text or "compute" in text


def test_context_skill_has_cache_hit_skip():
    text = _skill_text("context")
    assert "Cache hit" in text or "cache hit" in text