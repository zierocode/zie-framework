"""
Tests that bash injection patterns are present in zie-* command files.
All assertions are pure string checks — no subprocess execution.
"""

import re
from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestZieImplementInjections:
    def setup_method(self):
        self.content = (COMMANDS_DIR / "implement.md").read_text()

    def test_git_log_injection_present(self):
        assert "!`git log -5 --oneline`" in self.content

    def test_git_status_injection_present(self):
        assert "!`git status --short`" in self.content

    def test_no_knowledge_hash_injection(self):
        """knowledge-hash.py removed from implement.md — drift handled by session-resume."""
        assert "knowledge-hash.py" not in self.content

    def test_injections_in_preflight_section(self):
        inject_pos = self.content.find("!`git log -5 --oneline`")
        preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
        steps_pos = self.content.find("## Steps")
        assert preflight_pos < inject_pos < steps_pos, (
            "git log injection must appear inside ตรวจสอบก่อนเริ่ม, before Steps"
        )


class TestZieStatusInjections:
    def setup_method(self):
        self.content = (COMMANDS_DIR / "status.md").read_text()

    def test_roadmap_head_injection_present(self):
        assert "!`cat zie-framework/ROADMAP.md | head -30`" in self.content

    def test_knowledge_hash_injection_present(self):
        assert "!`python3 hooks/knowledge-hash.py" in self.content

    def test_knowledge_hash_injection_has_fallback(self):
        assert (
            '2>/dev/null || echo "knowledge-hash: unavailable"`' in self.content
            or "2>/dev/null || echo 'knowledge-hash: unavailable'`" in self.content
        )

    def test_knowledge_hash_computed_once(self):
        """status.md must compute knowledge-hash exactly once (bang injection reused in step 4)."""
        count = self.content.count("knowledge-hash.py")
        assert count == 1, (
            f"knowledge-hash.py must appear exactly once in status.md (found {count}) "
            "— step 4 must reuse the bang-injected result, not re-run"
        )

    def test_step4_references_injected_hash(self):
        """Step 4 must reference the pre-injected hash variable, not run a Bash call."""
        assert "current_hash_injected" in self.content or "injected" in self.content.lower(), (
            "status.md step 4 must reference the bang-injected hash (current_hash_injected), not re-run Bash"
        )

    def test_injections_precede_first_step(self):
        inject_pos = self.content.find("!`cat zie-framework/ROADMAP.md")
        step1_pos = self.content.find("\n1. **Check initialization**")
        assert 0 < inject_pos < step1_pos, "ROADMAP injection must appear before first step"


class TestZieRetroInjections:
    def setup_method(self):
        self.content = (COMMANDS_DIR / "retro.md").read_text()

    def test_commits_since_tag_injection_present(self):
        expected = (
            "!`git log $(git describe --tags --abbrev=0 2>/dev/null || "
            "git rev-list --max-parents=0 HEAD)..HEAD --oneline`"
        )
        assert expected in self.content

    def test_git_log_injection_present(self):
        """At least one git log bang injection must exist in retro.md."""
        import re

        bangs = re.findall(r"!`git log[^`]+`", self.content)
        assert len(bangs) >= 1, f"retro.md must have at least one git log bang injection, found {len(bangs)}"

    def test_single_git_log_bang_with_fallback(self):
        """Only one git log bang allowed — the commits-since-tag injection (with fallback)."""
        import re

        bangs = re.findall(r"!`git log[^`]+`", self.content)
        assert len(bangs) == 1, (
            f"Expected exactly 1 git log bang (commits-since-tag with fallback), found {len(bangs)}: {bangs}"
        )

    def test_self_tuning_uses_git_log_raw_not_bash(self):
        """Self-tuning step must reference git_log_raw, not spawn a Bash git log call."""
        import re

        # Non-blocking self-tuning section is at the end (after Suggest next)
        start = self.content.find("Self-tuning proposals")
        if start == -1:
            import pytest

            pytest.skip("Self-tuning section not found")
        # Find the section (until next ### or end)
        next_section = self.content.find("\n###", start + 1)
        section = self.content[start:next_section] if next_section != -1 else self.content[start:]
        assert "git_log_raw" in section, "Self-tuning step must reference git_log_raw (not spawn Bash git log)"
        bash_git_log = re.findall(r"git log[^\n]*oneline", section)
        assert not bash_git_log, f"Self-tuning section must not contain bare git log calls: {bash_git_log}"

    def test_docs_sync_guard_uses_git_log_raw(self):
        """Docs-sync guard must reference git_log_raw, not run git log -1."""
        import re

        docs_sync_start = self.content.find("Docs-sync")
        if docs_sync_start == -1:
            import pytest

            pytest.skip("Docs-sync section not found")
        # Find the segment around docs-sync guard (first occurrence)
        segment = self.content[docs_sync_start : docs_sync_start + 500]
        # The skip-guard check should use git_log_raw not a fresh git log call
        bare_git_log = re.findall(r"`git log -1[^`]*`", segment)
        assert not bare_git_log, f"Docs-sync guard must use git_log_raw, not run fresh git log: {bare_git_log}"

    def test_no_tag_fallback_present(self):
        assert "git rev-list --max-parents=0 HEAD" in self.content

    def test_injections_in_preflight_section(self):
        inject_pos = self.content.find("!`git log $(git describe")
        preflight_pos = self.content.find("## ตรวจสอบก่อนเริ่ม")
        steps_pos = self.content.find("## Steps")
        assert preflight_pos < inject_pos < steps_pos, "Retro injections must appear inside ตรวจสอบก่อนเริ่ม, before Steps"


class TestNoUnboundedInjections:
    """Guard: no injection command is unbounded (no bare `git log` without -N or range)."""

    def _injections(self, filename: str) -> list:
        content = (COMMANDS_DIR / filename).read_text()
        return re.findall(r"!`([^`]+)`", content)

    def test_implement_injections_are_bounded(self):
        for cmd in self._injections("implement.md"):
            if "git log" in cmd:
                assert "-5" in cmd or "-20" in cmd or "..HEAD" in cmd, f"Unbounded git log in zie-implement.md: {cmd}"

    def test_status_injections_are_bounded(self):
        for cmd in self._injections("status.md"):
            if "cat" in cmd:
                assert "head -30" in cmd, f"Unbounded cat in zie-status.md: {cmd}"

    def test_retro_injections_are_bounded(self):
        for cmd in self._injections("retro.md"):
            if "git log" in cmd and "describe" not in cmd:
                assert "-50" in cmd or "-20" in cmd or "..HEAD" in cmd, f"Unbounded git log in zie-retro.md: {cmd}"
