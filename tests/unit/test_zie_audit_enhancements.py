from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def read_audit() -> str:
    return (COMMANDS_DIR / "zie-audit.md").read_text()


class TestHardDataPhase1:
    def test_pytest_cov_present(self):
        assert "pytest --cov" in read_audit(), \
            "Phase 1 must include pytest --cov run"

    def test_radon_cc_present(self):
        assert "radon cc" in read_audit(), \
            "Phase 1 must include radon cc run"

    def test_pip_audit_present(self):
        text = read_audit()
        assert "pip audit" in text or "npm audit" in text, \
            "Phase 1 must include pip audit or npm audit run"

    def test_hard_data_feeds_agents(self):
        text = read_audit()
        assert "hard_data" in text, \
            "Phase 1 must define a hard_data variable fed to agents"

    def test_graceful_skip_present(self):
        text = read_audit()
        assert "skip" in text.lower() or "unavailable" in text.lower(), \
            "Hard data block must note graceful skip when tools absent"


class TestHistoricalDiff:
    def test_since_last_audit_heading_present(self):
        text = read_audit()
        assert "Since last audit" in text or "Since Last Audit" in text, \
            "Audit must have a 'Since last audit' section"

    def test_evidence_glob_present(self):
        text = read_audit()
        assert "evidence/audit-" in text, \
            "Historical diff must glob evidence/audit-*.md"

    def test_skip_when_no_previous_audit(self):
        text = read_audit()
        assert "no previous audit" in text.lower() or "skip" in text.lower(), \
            "Historical diff must skip gracefully when no prior audit exists"

    def test_diff_positioned_before_phase5(self):
        text = read_audit()
        diff_pos = text.lower().find("since last audit")
        phase5_pos = text.find("## Phase 5")
        assert diff_pos != -1, "Since last audit section not found"
        assert diff_pos < phase5_pos, \
            "Historical diff must appear before Phase 5"


class TestVersionSpecificQueries:
    def test_version_specific_query_block_present(self):
        text = read_audit()
        assert "version" in text and "CVE" in text, \
            "Phase 3 must include version-specific CVE queries"

    def test_deps_loop_present(self):
        text = read_audit()
        assert "research_profile.deps" in text or "for dep" in text, \
            "Phase 3 must loop over research_profile.deps for version queries"

    def test_version_query_format(self):
        text = read_audit()
        assert ("{dep}" in text and "{version}" in text) or \
               ("<dep>" in text and "<version>" in text), \
            "Phase 3 must interpolate dep name and version into queries"

    def test_generic_queries_preserved(self):
        text = read_audit()
        assert "best practices" in text, \
            "Existing generic best-practices queries must be preserved"
        assert "security vulnerabilities checklist" in text, \
            "Existing security checklist queries must be preserved"


class TestAutoFixOffer:
    def test_auto_fix_section_present(self):
        text = read_audit()
        assert "auto-fix" in text.lower() or "auto_fix" in text.lower(), \
            "Phase 5 must contain an auto-fix offer section"

    def test_auto_fix_scoped_to_low_medium(self):
        text = read_audit()
        assert "Low" in text and "Medium" in text, \
            "Auto-fix offer must reference Low and Medium severity"
        assert "High" in text and "Critical" in text, \
            "Auto-fix offer must explicitly exclude High and Critical"

    def test_auto_fixable_tag_referenced(self):
        text = read_audit()
        assert "auto-fixable" in text, \
            "Auto-fix offer must check for auto-fixable tag on findings"

    def test_auto_fix_positioned_after_backlog_write(self):
        text = read_audit()
        backlog_pos = text.find("zie-framework/backlog/")
        autofix_pos = text.lower().find("auto-fix")
        assert backlog_pos != -1, "Backlog write section not found"
        assert autofix_pos != -1, "Auto-fix section not found"
        assert autofix_pos > backlog_pos, \
            "Auto-fix offer must appear after backlog items are written"

    def test_skip_when_no_auto_fixable(self):
        text = read_audit()
        assert "skip" in text.lower() or "none" in text.lower(), \
            "Auto-fix section must skip gracefully when no qualifying findings"
