"""Structural tests: commands must not use git add -A (security risk)."""
from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def test_chore_no_git_add_all():
    """commands/chore.md must not use git add -A as a command (stages untracked/sensitive files)."""
    import re
    text = (COMMANDS_DIR / "chore.md").read_text()
    # Reject 'git add -A' appearing as a shell command (not in a prohibition note)
    # A prohibition note looks like: (no `git add -A`) or "not use git add -A"
    # Strip those negation patterns before checking
    cleaned = re.sub(r'\(no\s+`git add -A`\)', '', text)
    cleaned = re.sub(r'not use.*git add -A', '', cleaned)
    cleaned = re.sub(r'git add -A.*avoided', '', cleaned)
    assert "git add -A" not in cleaned, (
        "commands/chore.md must not use 'git add -A' as a command — use targeted git add instead"
    )


def test_chore_targeted_git_add():
    """commands/chore.md must instruct targeted git add with specific files."""
    text = (COMMANDS_DIR / "chore.md").read_text()
    assert "git add <" in text or "specific files" in text or "specific-files" in text, (
        "commands/chore.md must instruct targeted git add (not git add -A)"
    )
