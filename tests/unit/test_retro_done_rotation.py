"""Tests for /zie-retro Done-rotation step (roadmap-done-rotation feature)."""
from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "zie-retro.md"


def _text():
    return CMD.read_text()


class TestDoneRotationPresent:
    def test_rotation_step_exists(self):
        assert "Done-rotation" in _text(), \
            "zie-retro.md must contain a Done-rotation step"

    def test_rotation_is_inline_not_agent(self):
        text = _text()
        rotation_start = text.find("Done-rotation (inline)")
        assert rotation_start != -1, "Done-rotation section must exist"
        # Find end of the section (next ### heading)
        next_section = text.find("\n###", rotation_start + 1)
        rotation_section = text[rotation_start:next_section] if next_section != -1 else text[rotation_start:]
        assert "Agent(" not in rotation_section, \
            "Done-rotation must be inline — no Agent( call allowed in rotation section"

    def test_rotation_has_early_exit_guard(self):
        assert "≤ 10 items" in _text() or "<= 10" in _text(), \
            "Done-rotation must have an early-exit guard for ≤10 items"

    def test_rotation_has_90_day_threshold(self):
        assert "90 days" in _text(), \
            "Done-rotation must have a 90-day archival threshold"

    def test_rotation_has_keep_10_rule(self):
        text = _text()
        assert "10 most-recent" in text or "keep the 10" in text, \
            "Done-rotation must keep the 10 most-recent items inline"

    def test_rotation_has_archive_path_formula(self):
        assert "ROADMAP-archive-YYYY-MM.md" in _text() or "archive/ROADMAP-archive" in _text(), \
            "Done-rotation must specify archive path formula"

    def test_rotation_is_append_only(self):
        text = _text()
        assert "append-only" in text.lower() or "never rewrite" in text.lower() or "never truncate" in text.lower(), \
            "Done-rotation must enforce append-only writes (never rewrite/truncate)"

    def test_rotation_keeps_no_date_items(self):
        text = _text()
        assert "no date" in text.lower() or "no parseable date" in text.lower(), \
            "Done-rotation must keep items with no parseable date inline (never archive)"


class TestAutoCommitExtended:
    def test_git_add_includes_roadmap(self):
        assert "zie-framework/ROADMAP.md" in _text(), \
            "Auto-commit git add must include zie-framework/ROADMAP.md"

    def test_git_add_includes_archive_glob(self):
        assert "archive/ROADMAP-archive-*.md" in _text(), \
            "Auto-commit git add must include archive/ROADMAP-archive-*.md glob"


class TestRotationPosition:
    def test_rotation_after_await_both(self):
        text = _text()
        await_pos = text.find("Await both")
        rotation_pos = text.find("Done-rotation")
        assert await_pos != -1 and rotation_pos != -1, \
            "Both 'Await both' and 'Done-rotation' must exist in zie-retro.md"
        assert await_pos < rotation_pos, \
            "Done-rotation must appear after 'Await both'"

    def test_rotation_before_auto_commit(self):
        text = _text()
        rotation_pos = text.find("Done-rotation")
        commit_pos = text.find("### Auto-commit")
        assert rotation_pos != -1 and commit_pos != -1, \
            "Both 'Done-rotation' and '### Auto-commit' must exist"
        assert rotation_pos < commit_pos, \
            "Done-rotation must appear before '### Auto-commit retro outputs'"
