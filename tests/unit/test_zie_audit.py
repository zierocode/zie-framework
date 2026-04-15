from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
COMMANDS = ROOT / "commands"
SKILL = ROOT / "skills" / "audit" / "SKILL.md"


def read_cmd(name):
    return (COMMANDS / f"{name}.md").read_text()


def read_skill():
    return SKILL.read_text()


class TestZieAuditCommand:
    def test_command_file_exists(self):
        assert (COMMANDS / "audit.md").exists(), \
            "commands/audit.md must exist"

    def test_allowed_tools_include_websearch_and_webfetch(self):
        content = read_cmd("audit")
        assert "WebSearch" in content, \
            "audit must include WebSearch for external research"
        assert "WebFetch" in content, \
            "audit must include WebFetch for external research"

    def test_has_research_profile(self):
        # Skill is canonical; command delegates
        content = read_skill()
        assert "stack" in content or "deps" in content, \
            "audit skill must build a research profile (stack, deps)"

    def test_has_three_dimensions(self):
        content = read_skill()
        assert "Security" in content, "audit skill must cover Security dimension"
        assert "Code Health" in content or "Quality" in content or "Lean" in content, \
            "audit skill must cover Code Health/Lean dimension"
        assert "Structural" in content or "Architecture" in content, \
            "audit skill must cover Structural/Architecture dimension"

    def test_research_sources_are_dynamic(self):
        content = read_skill()
        assert "stack" in content or "languages" in content or "deps" in content

    def test_has_external_research_phase(self):
        content = read_skill()
        assert "WebSearch" in content
        assert "external" in content.lower() or "research" in content.lower()

    def test_has_severity_and_scoring(self):
        content = read_skill()
        assert "CRITICAL" in content or "Critical" in content
        assert "HIGH" in content or "High" in content
        assert "score" in content.lower() or "severity" in content.lower()

    def test_has_backlog_integration(self):
        content = read_skill()
        assert "backlog" in content.lower()
        assert "ROADMAP" in content

    def test_has_synthesis_phase(self):
        content = read_skill()
        assert "Synthesis" in content or "synthesis" in content, \
            "audit skill must have a synthesis phase to consolidate findings"

    def test_report_saved(self):
        content = read_skill()
        assert "audit-" in content or "audit_" in content or "evidence" in content, \
            "audit report must be saved"

    def test_components_md_lists_zie_audit(self):
        components = ROOT / "zie-framework" / "project" / "components.md"
        content = components.read_text()
        assert "/audit" in content, \
            "project/components.md must list /audit command"
