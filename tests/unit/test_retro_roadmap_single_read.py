"""
Assert that /retro reads ROADMAP.md once at pre-flight and threads
roadmap_raw through all downstream sections (no re-reads).
"""
import re
from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "retro.md"


class TestRoadmapSingleRead:
    def test_preflight_binds_roadmap_raw(self):
        src = CMD.read_text()
        assert "roadmap_raw" in src, \
            "Pre-flight must bind roadmap_raw variable"

    def test_roadmap_raw_defined_before_steps(self):
        src = CMD.read_text()
        preflight_end = src.find("## Steps")
        raw_pos = src.find("roadmap_raw")
        assert raw_pos != -1, "roadmap_raw must be defined"
        assert raw_pos < preflight_end, \
            "roadmap_raw must be bound before ## Steps section"

    def test_done_write_uses_roadmap_raw(self):
        src = CMD.read_text()
        section_start = src.find("Update ROADMAP Done inline")
        assert section_start != -1, "Update ROADMAP Done inline section must exist"
        next_section = src.find("\n###", section_start + 1)
        section = src[section_start:next_section] if next_section != -1 else src[section_start:]
        assert "Read `zie-framework/ROADMAP.md`" not in section, \
            "Done-write section must not re-read ROADMAP.md — use roadmap_raw"
        assert "roadmap_raw" in section, \
            "Done-write section must use roadmap_raw binding"

    def test_done_rotation_uses_roadmap_raw(self):
        src = CMD.read_text()
        rotation_start = src.find("Done-rotation (inline)")
        assert rotation_start != -1, "Done-rotation section must exist"
        next_section = src.find("\n###", rotation_start + 1)
        section = src[rotation_start:next_section] if next_section != -1 else src[rotation_start:]
        assert "Read `## Done` from `zie-framework/ROADMAP.md`" not in section, \
            "Done-rotation must not re-read ROADMAP.md — use roadmap_raw"
        assert "roadmap_raw" in section, \
            "Done-rotation must use roadmap_raw binding"

    def test_roadmap_read_count(self):
        """ROADMAP.md must not appear as an explicit Read target (pre-flight uses grep/bind pattern)."""
        src = CMD.read_text()
        read_patterns = re.findall(r"Read `zie-framework/ROADMAP\.md`", src)
        assert len(read_patterns) == 0, \
            f"ROADMAP.md must not appear as explicit Read target after refactor; found {len(read_patterns)} occurrence(s)"
