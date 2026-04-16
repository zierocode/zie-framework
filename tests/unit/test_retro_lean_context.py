"""Structural tests: zie-retro.md must pre-extract Done section for agents."""

from pathlib import Path

RETRO_MD = Path(__file__).parents[2] / "commands" / "retro.md"


class TestRetroLeanContext:
    def _src(self) -> str:
        return RETRO_MD.read_text()

    def test_compact_bundle_has_done_section_current(self):
        """Compact JSON bundle must include done_section_current field."""
        assert "done_section_current" in self._src(), (
            "zie-retro.md compact JSON bundle must include 'done_section_current' key"
        )

    def test_adr_write_step_present(self):
        """ADR inline write step must exist in zie-retro.md."""
        src = self._src()
        assert "Write ADR" in src or "Write` →" in src, "zie-retro.md must have an inline ADR write step"
        # done_section_current is defined in compact bundle, available to inline steps
        assert "done_section_current" in src, "compact bundle must include done_section_current for ADR/ROADMAP writes"

    def test_roadmap_update_step_present(self):
        """ROADMAP Done update step must exist in retro.md."""
        src = self._src()
        assert "ROADMAP Done" in src, "retro.md must have a ROADMAP Done update step"
        assert "done_section_current" in src, "compact bundle must include done_section_current for ROADMAP update"

    def test_agents_do_not_re_read_full_roadmap(self):
        """Agent prompts must not instruct agents to re-read the full ROADMAP file."""
        src = self._src()
        agents_section_start = src.find("### บันทึก ADRs + อัปเดต ROADMAP")
        if agents_section_start == -1:
            agents_section_start = src.find("ADRs")
        assert agents_section_start != -1, "ADRs section not found"
        agents_region = src[agents_section_start:]
        assert "re-read ROADMAP" not in agents_region, (
            "Agent prompts must not instruct re-reading ROADMAP — use done_section_current instead"
        )
        assert "read full" not in agents_region.lower(), "Agent prompts must not instruct reading the full ROADMAP file"
