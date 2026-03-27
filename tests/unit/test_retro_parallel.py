"""Tests for zie-retro.md parallel Agent calls for ADR + ROADMAP update."""
from pathlib import Path

RETRO_MD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


def test_retro_has_parallel_agent_note():
    """zie-retro.md must document parallel ADR + ROADMAP agent execution."""
    text = RETRO_MD.read_text()
    assert "run_in_background" in text, (
        "zie-retro.md must use run_in_background for parallel agents"
    )
    assert (
        "simultaneous" in text.lower()
        or "parallel" in text.lower()
        or "concurrent" in text.lower()
    ), "zie-retro.md must note parallel/concurrent execution"


def test_retro_brain_store_after_agents():
    """Brain store section must appear after parallel agent section."""
    text = RETRO_MD.read_text()
    agent_pos = text.find("run_in_background")
    # Use the brain-store section heading, not the frontmatter occurrence
    brain_pos = text.find("บันทึกสู่ brain")
    assert agent_pos != -1, "run_in_background not found"
    assert brain_pos != -1, "brain store section not found"
    assert agent_pos < brain_pos, (
        "Brain store must appear after parallel agent invocation"
    )


def test_retro_failure_mode_documented():
    """Failure handling for parallel agents must be documented."""
    text = RETRO_MD.read_text()
    assert "fail" in text.lower() or "fallback" in text.lower(), (
        "zie-retro.md must document failure handling for parallel agents"
    )
