"""Integration tests: verify CLAUDE.md documents the hook output convention."""
from pathlib import Path

CLAUDE_MD = Path(__file__).parents[2] / "CLAUDE.md"


def read_claude_md() -> str:
    return CLAUDE_MD.read_text()


# ── T5: Hook Output Convention ────────────────────────────────────────────────

def test_claude_md_hook_output_convention_section():
    content = read_claude_md()
    assert "Hook Output Convention" in content, (
        "CLAUDE.md must have a Hook Output Convention subsection"
    )


def test_claude_md_info_level_scope():
    content = read_claude_md()
    assert "INFO" in content or "INFO-level" in content, (
        "CLAUDE.md hook convention must specify INFO-level scope"
    )


def test_claude_md_compliant_hooks_named():
    content = read_claude_md()
    assert "wip-checkpoint" in content and "task-completed-gate" in content, (
        "CLAUDE.md must name wip-checkpoint and task-completed-gate as compliant"
    )


def test_claude_md_no_code_changes_needed():
    content = read_claude_md()
    assert "no" in content.lower() and "code changes" in content.lower(), (
        "CLAUDE.md must state no hook code changes are required"
    )
