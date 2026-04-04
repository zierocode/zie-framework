"""Structural tests: /status must include a Framework Health section."""
from pathlib import Path
import os

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATUS_CMD = Path(REPO_ROOT) / "commands" / "status.md"


class TestStatusFrameworkHealthSection:
    def _src(self):
        return STATUS_CMD.read_text()

    def test_framework_health_heading_present(self):
        assert "Framework Health" in self._src(), \
            "status.md must include a Framework Health section"

    def test_safety_check_mode_row_present(self):
        assert "safety_check_mode" in self._src(), \
            "status.md must surface safety_check_mode in Framework Health"

    def test_zie_memory_row_present(self):
        src = self._src()
        assert "zie-memory" in src or "zie_memory" in src, \
            "status.md must surface zie-memory status in Framework Health"

    def test_playwright_row_present(self):
        assert "playwright" in self._src(), \
            "status.md must surface playwright status in Framework Health"

    def test_stop_failures_section_present(self):
        assert "Stop failures" in self._src(), \
            "status.md must include Stop failures subsection"

    def test_stopfailure_log_path_documented(self):
        assert "failure-log" in self._src(), \
            "status.md must document the stopfailure-log path"

    def test_last_5_entries_instruction_present(self):
        src = self._src()
        assert "last 5" in src or "tail" in src, \
            "status.md must instruct tail/last-5 entries from stopfailure-log"

    def test_missing_log_fallback_documented(self):
        assert "No stop failures" in self._src(), \
            "status.md must document 'No stop failures recorded' fallback"

    def test_line_truncation_documented(self):
        assert "120" in self._src(), \
            "status.md must document 120-char truncation for MD013 compliance"
