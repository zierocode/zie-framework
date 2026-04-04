"""
Branding compliance tests — zie-framework.
Verify: no ASCII boxes, Thai phase names, handoff blocks present.
"""

import glob
import os

COMMANDS_DIR = "commands"
SKILLS_DIR = "skills"

# Only check for ┌ (box top-left corner) — unambiguous indicator of ASCII box art.
# ─ and └ appear legitimately in directory tree examples inside code blocks.
ASCII_BOX_CHARS = ["┌"]


def read_command(name):
    path = os.path.join(COMMANDS_DIR, f"{name}.md")
    with open(path) as f:
        return f.read()


def read_skill(name):
    path = os.path.join(SKILLS_DIR, name, "SKILL.md")
    with open(path) as f:
        return f.read()


class TestNoAsciiBoxes:
    def test_no_ascii_boxes_in_commands(self):
        """ทุก command file ต้องไม่มี ASCII box characters."""
        command_files = glob.glob(os.path.join(COMMANDS_DIR, "*.md"))
        assert command_files, "No command files found"
        violations = []
        for path in command_files:
            content = open(path).read()
            for char in ASCII_BOX_CHARS:
                if char in content:
                    violations.append(f"{path}: contains '{char}'")
        assert not violations, "ASCII box chars found:\n" + "\n".join(violations)

    def test_no_ascii_boxes_in_skills(self):
        """ทุก skill file ต้องไม่มี ASCII box characters."""
        skill_files = glob.glob(os.path.join(SKILLS_DIR, "*", "SKILL.md"))
        assert skill_files, "No skill files found"
        violations = []
        for path in skill_files:
            content = open(path).read()
            for char in ASCII_BOX_CHARS:
                if char in content:
                    violations.append(f"{path}: contains '{char}'")
        assert not violations, "ASCII box chars found:\n" + "\n".join(violations)

    def test_status_uses_markdown_table(self):
        """zie-status.md ต้องไม่มี ASCII box — ใช้ markdown table แทน."""
        content = read_command("status")
        for char in ASCII_BOX_CHARS:
            assert char not in content, (
                f"zie-status.md ยังมี ASCII box char '{char}' — ต้องใช้ markdown table"
            )


class TestPhaseLabelsRenamed:
    def test_phase_labels_renamed_implement(self):
        """zie-implement.md ต้องไม่มี 'Gate 1 —' หรือ 'Phase 1' pattern."""
        content = read_command("implement")
        assert "Gate 1 —" not in content, "zie-implement.md ยังมี 'Gate 1 —'"
        assert "Gate 2 —" not in content, "zie-implement.md ยังมี 'Gate 2 —'"

    def test_phase_labels_renamed_fix(self):
        """zie-fix.md ต้องไม่มี 'Phase 1 —' pattern."""
        content = read_command("fix")
        assert "Phase 1 —" not in content, "zie-fix.md ยังมี 'Phase 1 —'"
        assert "Phase 2 —" not in content, "zie-fix.md ยังมี 'Phase 2 —'"

    def test_phase_labels_renamed_release(self):
        """zie-release.md ต้องไม่มี 'Gate 1 —' pattern."""
        content = read_command("release")
        assert "Gate 1 —" not in content, "zie-release.md ยังมี 'Gate 1 —'"
        assert "Gate 2 —" not in content, "zie-release.md ยังมี 'Gate 2 —'"

    def test_preflight_renamed_to_thai(self):
        """commands ที่ควรเปลี่ยน Pre-flight → ตรวจสอบก่อนเริ่ม."""
        for cmd in ["implement", "fix", "release", "backlog", "plan", "retro"]:
            content = read_command(cmd)
            assert "## Pre-flight" not in content, (
                f"zie-{cmd}.md ยังมี '## Pre-flight' — ต้องเปลี่ยนเป็น '## ตรวจสอบก่อนเริ่ม'"
            )


class TestHandoffBlocks:
    def test_handoff_block_in_implement(self):
        """zie-implement.md ต้องมี '## ขั้นตอนถัดไป' block."""
        content = read_command("implement")
        assert "ขั้นตอนถัดไป" in content, "zie-implement.md ไม่มี handoff block '## ขั้นตอนถัดไป'"

    def test_handoff_block_in_fix(self):
        """zie-fix.md ต้องมี '## ขั้นตอนถัดไป' block."""
        content = read_command("fix")
        assert "ขั้นตอนถัดไป" in content, "zie-fix.md ไม่มี handoff block '## ขั้นตอนถัดไป'"
