from pathlib import Path

CONVENTIONS = Path(__file__).parents[2] / "zie-framework" / "project" / "command-conventions.md"


def test_conventions_file_exists():
    assert CONVENTIONS.exists(), "command-conventions.md must exist"


def test_conventions_has_preflight_heading():
    text = CONVENTIONS.read_text()
    assert "## Pre-flight" in text, "command-conventions.md must have ## Pre-flight heading"


def test_conventions_defines_3_steps():
    text = CONVENTIONS.read_text()
    assert "zie-framework/" in text
    assert ".config" in text
    assert "ROADMAP" in text


def test_conventions_has_anchor():
    text = CONVENTIONS.read_text()
    assert "pre-flight" in text.lower()
