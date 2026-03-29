"""Structural tests: zie-retro.md must pre-extract Done section for agents."""
from pathlib import Path

RETRO_MD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


class TestRetroLeanContext:
    def _src(self) -> str:
        return RETRO_MD.read_text()

    def test_compact_bundle_has_done_section_current(self):
        """Compact JSON bundle must include done_section_current field."""
        assert "done_section_current" in self._src(), (
            "zie-retro.md compact JSON bundle must include 'done_section_current' key"
        )

    def test_adr_agent_receives_done_section_current(self):
        """ADR background agent prompt must reference done_section_current."""
        src = self._src()
        adr_agent_pos = src.find("Write ADRs")
        assert adr_agent_pos != -1, "ADR agent invocation not found in zie-retro.md"
        region = src[max(0, adr_agent_pos - 100):adr_agent_pos + 500]
        assert "done_section_current" in region, (
            "ADR agent prompt must reference done_section_current to avoid re-reading ROADMAP"
        )

    def test_roadmap_agent_receives_done_section_current(self):
        """ROADMAP update background agent prompt must reference done_section_current."""
        src = self._src()
        roadmap_agent_pos = src.find("Update ROADMAP Done section")
        assert roadmap_agent_pos != -1, "ROADMAP update agent invocation not found"
        region = src[max(0, roadmap_agent_pos - 100):roadmap_agent_pos + 500]
        assert "done_section_current" in region, (
            "ROADMAP agent prompt must reference done_section_current"
        )

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
        assert "read full" not in agents_region.lower(), (
            "Agent prompts must not instruct reading the full ROADMAP file"
        )
