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
        assert "research_profile" in content, \
            "Phase 1 must build a research_profile struct"

    def test_has_all_9_dimensions(self):
        content = read_cmd("zie-audit")
        dimensions = [
            "Security", "Lean", "Quality", "Docs", "Architecture",
            "Performance", "Depend", "Developer", "Standards",
        ]
        for dim in dimensions:
            assert dim in content, \
                f"zie-audit must cover the {dim} dimension"

    def test_research_sources_are_dynamic(self):
        content = read_cmd("zie-audit")
        assert "research_profile" in content
        assert "languages" in content or "project_type" in content

    def test_has_external_research_phase(self):
        content = read_cmd("zie-audit")
        assert "WebSearch" in content
        assert "external" in content.lower() or "research" in content.lower()

    def test_has_severity_and_scoring(self):
        content = read_cmd("zie-audit")
        assert "Critical" in content
        assert "High" in content
        assert "/100" in content or "score" in content.lower()

    def test_has_backlog_integration(self):
        content = read_cmd("zie-audit")
        assert "backlog" in content.lower()
        assert "ROADMAP" in content

    def test_has_focus_flag(self):
        content = read_cmd("zie-audit")
        assert "--focus" in content

    def test_evidence_saved_locally(self):
        content = read_cmd("zie-audit")
        assert "evidence/" in content, \
            "audit report must be saved to evidence/ (gitignored)"

    def test_components_md_lists_zie_audit(self):
        components = ROOT / "zie-framework" / "project" / "components.md"
        content = components.read_text()
        assert "/zie-audit" in content, \
            "project/components.md must list /zie-audit command"
