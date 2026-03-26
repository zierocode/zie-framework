from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
COMMANDS = ROOT / "commands"


def read_cmd(name):
    return (COMMANDS / f"{name}.md").read_text()


class TestZieAuditCommand:
    def test_command_file_exists(self):
        assert (COMMANDS / "zie-audit.md").exists(), \
            "commands/zie-audit.md must exist"

    def test_allowed_tools_include_websearch_and_webfetch(self):
        content = read_cmd("zie-audit")
        assert "WebSearch" in content, \
            "zie-audit must include WebSearch for external research"
        assert "WebFetch" in content, \
            "zie-audit must include WebFetch for external research"

    def test_has_research_profile(self):
        content = read_cmd("zie-audit")
        assert "stack" in content or "deps" in content, \
            "Phase 1 must build a research profile (stack, deps)"

    def test_has_three_dimensions(self):
        content = read_cmd("zie-audit")
        assert "Security" in content, "zie-audit must cover Security dimension"
        assert "Code Health" in content or "Quality" in content, \
            "zie-audit must cover Code Health dimension"
        assert "Structural" in content or "Architecture" in content, \
            "zie-audit must cover Structural dimension"

    def test_research_sources_are_dynamic(self):
        content = read_cmd("zie-audit")
        assert "stack" in content or "languages" in content or "deps" in content

    def test_has_external_research_phase(self):
        content = read_cmd("zie-audit")
        assert "WebSearch" in content
        assert "external" in content.lower() or "research" in content.lower()

    def test_has_severity_and_scoring(self):
        content = read_cmd("zie-audit")
        assert "CRITICAL" in content or "Critical" in content
        assert "HIGH" in content or "High" in content
        assert "score" in content.lower() or "severity" in content.lower()

    def test_has_backlog_integration(self):
        content = read_cmd("zie-audit")
        assert "backlog" in content.lower()
        assert "ROADMAP" in content

    def test_has_synthesis_phase(self):
        content = read_cmd("zie-audit")
        assert "Synthesis" in content or "synthesis" in content, \
            "zie-audit must have a synthesis phase to consolidate findings"

    def test_report_saved(self):
        content = read_cmd("zie-audit")
        assert "audit-" in content or "audit_" in content, \
            "audit report must be saved with an audit-<date> filename"

    def test_components_md_lists_zie_audit(self):
        components = ROOT / "zie-framework" / "project" / "components.md"
        content = components.read_text()
        assert "/zie-audit" in content, \
            "project/components.md must list /zie-audit command"
