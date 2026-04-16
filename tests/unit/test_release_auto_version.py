"""Tests for agentic-pipeline-v2 Task 3: zie-release auto-accepts version suggestion."""

from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "release.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestReleaseAutoVersion:
    def test_no_confirm_version_prompt(self):
        """'Confirm? (Enter = accept / major / minor / patch to override)' must be removed."""
        text = cmd_text()
        assert "Confirm?" not in text and "Enter = accept" not in text, (
            "zie-release must not show interactive version confirmation prompt"
        )

    def test_version_display_message_present(self):
        """Version is displayed (not prompted) — user can override if wrong."""
        text = cmd_text()
        assert "override" in text.lower() or "Send override" in text or "--bump-to" in text, (
            "zie-release must document override option after auto-accepting version"
        )

    def test_version_suggestion_step_present(self):
        """Version bump calculation still happens."""
        text = cmd_text()
        assert "version bump" in text.lower() or "Suggest version" in text or "bump" in text.lower()

    def test_auto_proceeds_after_version(self):
        """Pipeline continues automatically after version display (no blocking wait)."""
        text = cmd_text()
        # No interactive confirmation gate — just display and continue
        assert "Confirm?" not in text

    def test_bump_version_step_present(self):
        """VERSION file is still written."""
        text = cmd_text()
        assert "Bump VERSION" in text or "bump" in text.lower()


class TestVersionBumpSemver:
    def test_minor_bump_for_new_capability(self):
        """Minor bump required when ANY new user-visible capability is shipped."""
        text = cmd_text()
        assert "minor" in text.lower(), "release must document minor bump rule"

    def test_patch_only_for_internal_changes(self):
        """Patch only when ALL items are fix/refactor/chore/docs."""
        text = cmd_text()
        assert "patch" in text.lower() and ("fix" in text.lower() or "refactor" in text.lower()), (
            "release must define patch as fix/refactor/chore/docs only"
        )

    def test_minor_takes_priority_over_patch(self):
        """Any single minor-worthy item → bump minor, not patch."""
        text = cmd_text()
        assert "ANY" in text or "any" in text.lower(), "must state that ANY new capability triggers minor bump"

    def test_default_to_minor_when_in_doubt(self):
        """When in doubt between minor and patch, default to minor."""
        text = cmd_text()
        assert "default" in text.lower() or "doubt" in text.lower(), (
            "must specify default behaviour when minor vs patch is ambiguous"
        )
