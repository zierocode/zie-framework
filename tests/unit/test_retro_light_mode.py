from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "retro.md"


def text():
    return CMD.read_text()


class TestRetroLightMode:
    def test_adr_required_tag_gate(self):
        assert "adr: required" in text(), "retro.md must gate full ADR on <!-- adr: required --> tag in plan"

    def test_roadmap_update_always_runs(self):
        t = text()
        assert "ROADMAP" in t and "Done" in t, "ROADMAP Done update must always run (not gated)"

    def test_adr_summary_always_runs(self):
        assert "ADR-000-summary" in text(), "ADR-000-summary.md update must always run (not gated)"

    def test_full_adr_gated_description(self):
        t = text().lower()
        assert "adr: required" in text() and ("skip" in t or "only" in t or "gated" in t), (
            "retro must describe skipping full ADR when tag absent"
        )
