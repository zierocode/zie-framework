"""Verify retro-format skill contains the compaction step."""
from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "retro-format" / "SKILL.md"


def test_skill_contains_compaction_step():
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert "compact_roadmap_done" in content, (
        "retro-format/SKILL.md must call compact_roadmap_done after ROADMAP update"
    )


def test_skill_contains_compaction_log_messages():
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert "no archival needed" in content, (
        "retro-format/SKILL.md must include 'no archival needed' message variant"
    )
    assert "features shipped" in content, (
        "retro-format/SKILL.md must include 'features shipped' message variant"
    )


def test_skill_contains_guard_for_missing_roadmap():
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert any(word in content for word in ("skip", "missing", "not found", "cannot")), (
        "retro-format/SKILL.md compaction step must guard against missing ROADMAP"
    )
