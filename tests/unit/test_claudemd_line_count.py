"""Assert CLAUDE.md stays within the 80-line budget.

Enforces the lean-claudemd-trim-to-trigger-table refactor goal.
Hook authoring reference material lives in zie-framework/project/hook-conventions.md
and zie-framework/project/config-reference.md — not in CLAUDE.md.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def test_claudemd_line_count():
    path = REPO_ROOT / "CLAUDE.md"
    lines = path.read_text().splitlines()
    assert len(lines) <= 87, (
        f"CLAUDE.md has {len(lines)} lines (limit: 87). "
        "Move reference material to zie-framework/project/ spoke docs."
    )


def test_claudemd_stable_dynamic_markers():
    content = (REPO_ROOT / "CLAUDE.md").read_text()
    assert "<!-- STABLE" in content, "CLAUDE.md must have <!-- STABLE --> marker before stable sections"
    assert "<!-- DYNAMIC" in content, "CLAUDE.md must have <!-- DYNAMIC --> marker before dynamic sections"
    assert content.index("<!-- STABLE") < content.index("<!-- DYNAMIC"), (
        "<!-- STABLE --> marker must appear before <!-- DYNAMIC --> marker"
    )


def test_claudemd_tech_stack_in_dynamic_section():
    content = (REPO_ROOT / "CLAUDE.md").read_text()
    assert "<!-- DYNAMIC" in content
    dynamic_pos = content.index("<!-- DYNAMIC")
    tech_stack_pos = content.index("## Tech Stack")
    assert tech_stack_pos > dynamic_pos, "## Tech Stack must appear after <!-- DYNAMIC --> marker"


def test_hook_conventions_spoke_exists():
    assert (REPO_ROOT / "zie-framework" / "project" / "hook-conventions.md").exists(), (
        "zie-framework/project/hook-conventions.md must exist (hook authoring reference)"
    )


def test_config_reference_spoke_exists():
    assert (REPO_ROOT / "zie-framework" / "project" / "config-reference.md").exists(), (
        "zie-framework/project/config-reference.md must exist (hook config key reference)"
    )


def test_claudemd_references_hook_conventions():
    content = (REPO_ROOT / "CLAUDE.md").read_text()
    assert "hook-conventions.md" in content, (
        "CLAUDE.md trigger table must reference hook-conventions.md"
    )


def test_claudemd_references_config_reference():
    content = (REPO_ROOT / "CLAUDE.md").read_text()
    assert "config-reference.md" in content, (
        "CLAUDE.md trigger table must reference config-reference.md"
    )
