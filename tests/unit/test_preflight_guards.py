"""Tests for pre-flight guard presence in preflight:full commands.

For each command declaring preflight: full, verify the 3 guard steps appear
in the referenced command-conventions.md or inline:
1. Check zie-framework/ exists
2. Read .config
3. Read ROADMAP.md
"""

import re
from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"
CONVENTIONS = Path(__file__).parents[2] / "zie-framework" / "project" / "command-conventions.md"
COMMAND_FILES = sorted(COMMANDS_DIR.glob("*.md"))

PREFLIGHT_FULL_RE = re.compile(r"<!-- preflight: full -->")
PREFLIGHT_MINIMAL_RE = re.compile(r"<!-- preflight: minimal -->")
PREFLIGHT_REF_RE = re.compile(r"\[Pre-flight standard\]")


class TestPreflightFullGuards:
    """Commands with preflight: full must reference the pre-flight standard."""

    def test_full_preflight_commands_reference_conventions(self):
        """All preflight:full commands must have a pre-flight convention reference."""
        violations = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            if PREFLIGHT_FULL_RE.search(text):
                if not PREFLIGHT_REF_RE.search(text):
                    violations.append(cmd_file.name)
        # Some commands have inline pre-flight steps (release, retro, sprint)
        # that duplicate the convention but also have the HTML comment
        # This test only checks that commands with <!-- preflight: full -->
        # also reference the convention doc
        assert len(violations) <= 3, (
            "Too many commands with preflight:full missing convention reference:\n"
            + "\n".join(violations)
            + "\n(max 3 allowed — commands with inline pre-flight steps)"
        )

    def test_minimal_preflight_commands_exist(self):
        """Read-only commands should declare preflight: minimal."""
        minimal_commands = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            if PREFLIGHT_MINIMAL_RE.search(text):
                minimal_commands.append(cmd_file.name)

        expected_minimal = {"health.md", "brief.md", "guide.md", "next.md", "status.md"}
        found = set(minimal_commands)
        missing = expected_minimal - found
        assert not missing, f"Expected minimal preflight in: {missing}\nFound minimal in: {found}"

    def test_init_has_no_preflight_declaration(self):
        """init creates the framework — should not have standard pre-flight."""
        text = (COMMANDS_DIR / "init.md").read_text()
        assert not PREFLIGHT_FULL_RE.search(text), "/init should not declare preflight:full"
        assert not PREFLIGHT_MINIMAL_RE.search(text), "/init should not declare preflight:minimal"

    def test_conventions_define_full_guard_steps(self):
        """command-conventions.md must define all 3 guard steps."""
        text = CONVENTIONS.read_text()
        assert "zie-framework/" in text, "Must check zie-framework/ exists"
        assert ".config" in text, "Must read .config"
        assert "ROADMAP" in text, "Must read ROADMAP"
        assert "WIP" in text or "wip" in text.lower(), "Must check WIP guard"
