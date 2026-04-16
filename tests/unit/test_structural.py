"""Structural assertions for command/skill file size and composition."""

from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def test_audit_command_is_thin_dispatcher():
    """/audit must be a thin dispatcher (≤20 lines) — implementation lives in audit skill."""
    lines = (REPO_ROOT / "commands" / "audit.md").read_text().splitlines()
    assert len(lines) <= 20, (
        f"commands/audit.md has {len(lines)} lines (limit: 20). Move audit logic to skills/audit/SKILL.md."
    )


def test_audit_command_invokes_skill():
    """/audit must invoke Skill(zie-framework:audit)."""
    content = (REPO_ROOT / "commands" / "audit.md").read_text()
    assert "audit" in content, "commands/audit.md must invoke Skill(zie-framework:audit)"
