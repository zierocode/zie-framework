"""Structural tests: reviewer skills must reference cache helpers in Phase 1."""
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def _skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def test_spec_reviewer_references_get_cached_adrs():
    assert "get_cached_adrs" in _skill_text("spec-reviewer")


def test_spec_reviewer_references_write_adr_cache():
    assert "write_adr_cache" in _skill_text("spec-reviewer")


def test_plan_reviewer_references_get_cached_adrs():
    assert "get_cached_adrs" in _skill_text("plan-reviewer")


def test_plan_reviewer_references_write_adr_cache():
    assert "write_adr_cache" in _skill_text("plan-reviewer")


def test_impl_reviewer_references_get_cached_adrs():
    assert "get_cached_adrs" in _skill_text("impl-reviewer")


def test_impl_reviewer_references_write_adr_cache():
    assert "write_adr_cache" in _skill_text("impl-reviewer")


def test_impl_reviewer_references_adr_cache_path():
    assert "adr_cache_path" in _skill_text("impl-reviewer")
