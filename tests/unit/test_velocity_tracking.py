from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def read_status_command() -> str:
    return (COMMANDS_DIR / "status.md").read_text()


class TestVelocityTracking:
    def test_git_tag_command_present(self):
        text = read_status_command()
        assert "git log --tags" in text or "git log --tags --simplify-by-decoration" in text, \
            "zie-status.md must contain git log --tags command for velocity"

    def test_velocity_output_line_present(self):
        text = read_status_command()
        assert "Velocity" in text, \
            "zie-status.md must contain a Velocity output line"

    def test_graceful_fallback_present(self):
        text = read_status_command()
        assert "not enough releases yet" in text, \
            "zie-status.md must contain graceful fallback for <2 semver tags"
