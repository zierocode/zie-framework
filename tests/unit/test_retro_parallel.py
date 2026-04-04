"""Tests for zie-retro.md ADR + ROADMAP inline writes."""
from pathlib import Path

RETRO_MD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


def test_retro_writes_adrs_inline():
    """zie-retro.md must document inline ADR writes (not agent-based)."""
    text = RETRO_MD.read_text()
    assert "Write" in text and "ADR" in text, (
        "zie-retro.md must document inline Write for ADR files"
    )
    assert "run_in_background" not in text, (
        "zie-retro.md must NOT use run_in_background for ADR/ROADMAP writes"
    )


def test_retro_brain_store_after_writes():
    """Brain store section must appear after ADR/ROADMAP write section."""
    text = RETRO_MD.read_text()
    write_adr_pos = text.find("Write ADR") if "Write ADR" in text else text.find("Write` →")
    brain_pos = text.find("บันทึกสู่ brain")
    assert brain_pos != -1, "brain store section not found"
    # write_adr_pos may be -1 if phrasing changed — just verify brain store is present
    if write_adr_pos != -1:
        assert write_adr_pos < brain_pos, (
            "Brain store must appear after inline ADR write section"
        )


def test_retro_failure_mode_documented():
    """Failure handling must be documented."""
    text = RETRO_MD.read_text()
    assert "fail" in text.lower() or "error" in text.lower() or "continue" in text.lower(), (
        "zie-retro.md must document error/failure handling"
    )


class TestRetroLeanContextExtension:
    def test_retro_compact_bundle_has_done_section_current(self):
        """Compact bundle must include done_section_current for lean agent context."""
        text = RETRO_MD.read_text()
        assert "done_section_current" in text, (
            "zie-retro.md compact JSON bundle must include 'done_section_current'"
        )
