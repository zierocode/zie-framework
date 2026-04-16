"""Tests for tdd-loop/SKILL.md — verifies new make test-fast/test-ci references."""

from pathlib import Path

SKILL = Path(__file__).parents[2] / "skills" / "tdd-loop" / "SKILL.md"


def _text():
    return SKILL.read_text()


def test_skill_file_exists():
    assert SKILL.exists()


def test_red_phase_uses_test_fast():
    text = _text()
    red_section = text.split("### GREEN")[0]
    assert "make test-fast" in red_section, "RED phase must reference make test-fast"


def test_green_phase_uses_test_fast():
    text = _text()
    green_section = text.split("### GREEN")[1].split("### REFACTOR")[0]
    assert "make test-fast" in green_section, "GREEN phase must reference make test-fast"


def test_refactor_phase_uses_test_ci():
    text = _text()
    refactor_section = text.split("### REFACTOR")[1]
    assert "make test-ci" in refactor_section, "REFACTOR phase must reference make test-ci"


def test_original_structure_preserved():
    text = _text()
    assert "### RED" in text
    assert "### GREEN" in text
    assert "### REFACTOR" in text
