"""Integration tests: verify hook output convention is documented."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CLAUDE_MD = REPO_ROOT / "CLAUDE.md"
HOOK_CONVENTIONS = REPO_ROOT / "zie-framework" / "project" / "hook-conventions.md"


def read_claude_md() -> str:
    return CLAUDE_MD.read_text()


def read_hook_conventions() -> str:
    return HOOK_CONVENTIONS.read_text()


# ── T5: Hook Output Convention ────────────────────────────────────────────────

def test_claude_md_hook_output_convention_section():
    content = read_claude_md()
    assert "Hook Output Convention" in content, (
        "CLAUDE.md must reference Hook Output Convention (trigger table or section)"
    )


def test_hook_conventions_info_level_scope():
    content = read_hook_conventions()
    assert "INFO" in content or "INFO-level" in content, (
        "hook-conventions.md must specify INFO-level scope"
    )


def test_hook_conventions_compliant_hooks_named():
    content = read_hook_conventions()
    assert "wip-checkpoint" in content and "task-completed-gate" in content, (
        "hook-conventions.md must name wip-checkpoint and task-completed-gate as compliant"
    )


def test_hook_conventions_no_code_changes_needed():
    content = read_hook_conventions()
    assert "no" in content.lower() and "code changes" in content.lower(), (
        "hook-conventions.md must state no hook code changes are required"
    )
