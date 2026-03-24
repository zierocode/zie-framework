"""
Tests that bash injection patterns are present in zie-* command files.
All assertions are pure string checks — no subprocess execution.
"""
import re
from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestZieImplementInjections:
    def setup_method(self):
        self.content = (COMMANDS_DIR / "zie-implement.md").read_text()

    def test_git_log_injection_present(self):
        assert "!`git log -5 --oneline`" in self.content

    def test_git_status_injection_present(self):
        assert "!`git status --short`" in self.content

    def test_knowledge_hash_injection_present(self):
        assert (
            "!`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now"
            in self.content
        )

    def test_knowledge_hash_injection_has_fallback(self):
        assert (
            '2>/dev/null || echo "knowledge-hash: unavailable"`' in self.content
            or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
        )

    def test_claude_skill_dir_used_for_script_path(self):
        assert "${CLAUDE_SKILL_DIR}" in self.content

    def test_injections_in_preflight_section(self):
        inject_pos = self.content.find("!`git log -5 --oneline`")
        preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
        steps_pos = self.content.find("## Steps")
        assert preflight_pos < inject_pos < steps_pos, (
            "git log injection must appear inside ตรวจสอบก่อนเริ่ม, before Steps"
        )


class TestZieStatusInjections:
    def setup_method(self):
        self.content = (COMMANDS_DIR / "zie-status.md").read_text()

    def test_roadmap_head_injection_present(self):
        assert "!`cat zie-framework/ROADMAP.md | head -30`" in self.content

    def test_knowledge_hash_injection_present(self):
        assert "!`python3 hooks/knowledge-hash.py" in self.content

    def test_knowledge_hash_injection_has_fallback(self):
        assert (
            '2>/dev/null || echo "knowledge-hash: unavailable"`' in self.content
            or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
        )

    def test_injections_precede_first_step(self):
        inject_pos = self.content.find("!`cat zie-framework/ROADMAP.md")
        steps_pos = self.content.find("## Steps")
        step1_pos = self.content.find("\n1. **Check initialization**")
        assert steps_pos < inject_pos < step1_pos, (
            "ROADMAP injection must appear inside Steps section, before step 1"
        )


class TestZieRetroInjections:
    def setup_method(self):
        self.content = (COMMANDS_DIR / "zie-retro.md").read_text()

    def test_commits_since_tag_injection_present(self):
        expected = (
            "!`git log $(git describe --tags --abbrev=0 2>/dev/null || "
            "git rev-list --max-parents=0 HEAD)..HEAD --oneline`"
        )
        assert expected in self.content

    def test_recent_activity_injection_present(self):
        assert "!`git log -20 --oneline`" in self.content

    def test_no_tag_fallback_present(self):
        assert "git rev-list --max-parents=0 HEAD" in self.content

    def test_injections_in_preflight_section(self):
        inject_pos = self.content.find("!`git log $(git describe")
        preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
        steps_pos = self.content.find("## Steps")
        assert preflight_pos < inject_pos < steps_pos, (
            "Retro injections must appear inside ตรวจสอบก่อนเริ่ม, before Steps"
        )


class TestNoUnboundedInjections:
    """Guard: no injection command is unbounded (no bare `git log` without -N or range)."""

    def _injections(self, filename: str) -> list:
        content = (COMMANDS_DIR / filename).read_text()
        return re.findall(r"!`([^`]+)`", content)

    def test_implement_injections_are_bounded(self):
        for cmd in self._injections("zie-implement.md"):
            if "git log" in cmd:
                assert (
                    "-5" in cmd or "-20" in cmd or "..HEAD" in cmd
                ), f"Unbounded git log in zie-implement.md: {cmd}"

    def test_status_injections_are_bounded(self):
        for cmd in self._injections("zie-status.md"):
            if "cat" in cmd:
                assert "head -30" in cmd, f"Unbounded cat in zie-status.md: {cmd}"

    def test_retro_injections_are_bounded(self):
        for cmd in self._injections("zie-retro.md"):
            if "git log" in cmd and "describe" not in cmd:
                assert "-20" in cmd or "..HEAD" in cmd, (
                    f"Unbounded git log in zie-retro.md: {cmd}"
                )
