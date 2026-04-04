from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def read_command(filename: str) -> str:
    return (COMMANDS_DIR / filename).read_text()


class TestZieImplement:
    def test_now_section_read_instruction_present(self):
        text = read_command("implement.md")
        assert "Now" in text, "zie-implement.md must reference Now section"

    def test_no_unqualified_full_roadmap_read(self):
        text = read_command("implement.md")
        assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
            "zie-implement.md must not contain an unqualified full ROADMAP.md read"


class TestZieStatus:
    def test_now_section_targeted_read_present(self):
        text = read_command("status.md")
        assert "Now" in text, "zie-status.md must reference Now section"

    def test_next_done_count_instruction_present(self):
        text = read_command("status.md")
        assert "count" in text.lower() or "grep" in text.lower(), \
            "zie-status.md must instruct grep/count for Next and Done sections"

    def test_no_unqualified_full_roadmap_read(self):
        text = read_command("status.md")
        assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
            "zie-status.md must not contain an unqualified full ROADMAP.md read"


class TestZiePlan:
    def test_now_section_targeted_read_present(self):
        text = read_command("plan.md")
        assert "Now" in text, "zie-plan.md must reference Now section"

    def test_next_section_targeted_read_present(self):
        text = read_command("plan.md")
        assert "Next" in text, "zie-plan.md must reference Next section"

    def test_no_unqualified_full_roadmap_read(self):
        text = read_command("plan.md")
        assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
            "zie-plan.md must not contain an unqualified full ROADMAP.md read"


class TestZieSpec:
    def test_now_section_targeted_read_present(self):
        text = read_command("spec.md")
        assert "Now" in text, "zie-spec.md must reference Now section"

    def test_no_unqualified_full_roadmap_read(self):
        text = read_command("spec.md")
        assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
            "zie-spec.md must not contain an unqualified full ROADMAP.md read"


class TestZieRetro:
    def test_now_section_targeted_read_present(self):
        text = read_command("retro.md")
        assert "Now" in text, "zie-retro.md must reference Now section"

    def test_done_section_recent_limit_present(self):
        text = read_command("retro.md")
        assert "Done" in text, "zie-retro.md must reference Done section"
        assert "20" in text or "recent" in text.lower(), \
            "zie-retro.md must limit Done section read to recent items"

    def test_no_unqualified_full_roadmap_read(self):
        text = read_command("retro.md")
        assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
            "zie-retro.md must not contain an unqualified full ROADMAP.md read"


class TestZieRelease:
    def test_now_section_targeted_read_present(self):
        text = read_command("release.md")
        assert "Now" in text, "zie-release.md must reference Now section"

    def test_no_unqualified_full_roadmap_read(self):
        text = read_command("release.md")
        assert "Read `zie-framework/ROADMAP.md`\n" not in text, \
            "zie-release.md must not contain an unqualified full ROADMAP.md read"
