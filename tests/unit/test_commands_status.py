"""Structural tests: /status must include a Framework Health section."""

import os
from pathlib import Path

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STATUS_CMD = Path(REPO_ROOT) / "commands" / "status.md"


class TestStatusFrameworkHealthSection:
    def _src(self):
        return STATUS_CMD.read_text()

    def test_config_line_present(self):
        assert "config:" in self._src(), "status.md must include a config line showing safety/mem/pw/drift"

    def test_safety_mode_row_present(self):
        assert "safety=" in self._src(), "status.md must surface safety mode in config line"

    def test_memory_status_present(self):
        src = self._src()
        assert "mem=" in src or "zie-memory" in src or "zie_memory" in src, "status.md must surface memory status"

    def test_playwright_status_present(self):
        src = self._src()
        assert "pw=" in src or "playwright" in src, "status.md must surface playwright status"

    def test_failures_section_present(self):
        assert "failures:" in self._src(), "status.md must include failures subsection"

    def test_stopfailure_log_path_documented(self):
        assert "failure-log" in self._src(), "status.md must document the failure-log path"

    def test_last_5_entries_instruction_present(self):
        src = self._src()
        assert "last 5" in src or "tail" in src, "status.md must instruct tail/last-5 entries from failure-log"

    def test_missing_log_fallback_documented(self):
        src = self._src()
        assert "0 if missing" in src or "non-empty" in src, (
            "status.md must document fallback for empty/missing log files"
        )

    def test_line_truncation_documented(self):
        assert "120" in self._src(), "status.md must document 120-char truncation for MD013 compliance"
