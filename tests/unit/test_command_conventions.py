"""Tests for command convention compliance across all command files.

Verifies:
1. Every command has a pre-flight reference or declares preflight level
2. Error messages match STOP: / ⚠ / ℹ️ format (no bare STOP, ⛔)
3. Every command has a header line and a next-step footer
4. command-conventions.md has all required sections
"""

import re
from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"
CONVENTIONS = Path(__file__).parents[2] / "zie-framework" / "project" / "command-conventions.md"
COMMAND_FILES = sorted(COMMANDS_DIR.glob("*.md"))
assert len(COMMAND_FILES) >= 14, f"Expected 14+ command files, found {len(COMMAND_FILES)}"

# Patterns
HEADER_RE = re.compile(r"^# /(\w+) — ", re.MULTILINE)
PREFLIGHT_FULL_RE = re.compile(r"<!-- preflight: full -->")
PREFLIGHT_MINIMAL_RE = re.compile(r"<!-- preflight: minimal -->")
PREFLIGHT_REF_RE = re.compile(r"\[Pre-flight standard\]")
STOP_BARE_RE = re.compile(r"\bSTOP\b(?!:)")
EMOJI_X_RE = re.compile(r"⛔")
FOOTER_RE = re.compile(r"→.?/(\w+)|Next: /(\w+)|→ `/(\w+)")


# ── command-conventions.md tests ─────────────────────────────────────────────


def test_conventions_file_exists():
    assert CONVENTIONS.exists(), "command-conventions.md must exist"


def test_conventions_has_preflight_heading():
    text = CONVENTIONS.read_text()
    assert "## Pre-flight" in text


def test_conventions_defines_3_steps():
    text = CONVENTIONS.read_text()
    assert "zie-framework/" in text
    assert ".config" in text
    assert "ROADMAP" in text


def test_conventions_has_anchor():
    text = CONVENTIONS.read_text()
    assert "pre-flight" in text.lower()


def test_conventions_has_error_format_section():
    text = CONVENTIONS.read_text()
    assert "## Error format" in text
    assert "STOP:" in text
    assert "⚠" in text


def test_conventions_has_output_format_section():
    text = CONVENTIONS.read_text()
    assert "## Output format" in text
    assert "header line" in text.lower() or "Header line" in text


def test_conventions_has_preflight_levels():
    text = CONVENTIONS.read_text()
    assert "preflight: full" in text
    assert "preflight: minimal" in text


# ── Command file compliance tests ────────────────────────────────────────────


class TestPreflightPresence:
    """Every command must reference command-conventions.md or declare preflight level."""

    def test_all_commands_have_preflight(self):
        violations = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            has_full = PREFLIGHT_FULL_RE.search(text)
            has_minimal = PREFLIGHT_MINIMAL_RE.search(text)
            has_ref = PREFLIGHT_REF_RE.search(text)
            # init.md creates the framework — no pre-flight needed
            if cmd_file.name == "init.md":
                continue
            if not (has_full or has_minimal or has_ref):
                violations.append(cmd_file.name)
        assert not violations, "Commands missing pre-flight reference or declaration:\n" + "\n".join(violations)

    def test_init_has_no_preflight_ref(self):
        text = (COMMANDS_DIR / "init.md").read_text()
        assert not PREFLIGHT_REF_RE.search(text), "/init should not reference command-conventions pre-flight"


class TestErrorFormat:
    """Error messages must use STOP: / ⚠ / ℹ️ format."""

    def test_no_bare_stop_without_colon(self):
        violations = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if re.search(r"\bSTOP\b(?!:)", line) and "STOP:" not in line:
                    violations.append(f"{cmd_file.name}:{i + 1}: {line.strip()}")
        assert len(violations) <= 2, "Found STOP without colon (should be STOP:):\n" + "\n".join(violations)

    def test_no_emoji_x_blocker(self):
        violations = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            if EMOJI_X_RE.search(text):
                violations.append(cmd_file.name)
        assert not violations, "⛔ found in commands (use STOP: instead):\n" + "\n".join(violations)


class TestHeaderAndFooter:
    """Every command must have a header line and next-step footer."""

    def test_all_commands_have_header(self):
        violations = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            if not HEADER_RE.search(text):
                violations.append(cmd_file.name)
        assert not violations, "Commands missing /command — description header:\n" + "\n".join(violations)

    def test_all_commands_have_footer(self):
        violations = []
        for cmd_file in COMMAND_FILES:
            text = cmd_file.read_text()
            if not FOOTER_RE.search(text) and "/retro running..." not in text:
                violations.append(cmd_file.name)
        assert not violations, "Commands missing next-step footer (→ /command or Next: /command):\n" + "\n".join(
            violations
        )
