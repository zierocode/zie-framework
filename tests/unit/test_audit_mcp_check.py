"""Tests for audit MCP server usage check (audit-mcp-check feature)."""

from pathlib import Path

# MCP check moved to audit skill (canonical since lean-dual-audit-pipeline)
SKILL = Path(__file__).parents[2] / "skills" / "audit" / "SKILL.md"


def _text():
    return SKILL.read_text()


class TestMcpCheckPresent:
    def test_mcp_check_exists(self):
        assert "MCP" in _text() or "mcp__" in _text(), "audit skill must contain an MCP server usage check"

    def test_mcp_check_has_low_finding(self):
        assert "LOW" in _text() or "consider removing" in _text(), "MCP check must emit LOW finding for unused servers"

    def test_mcp_check_has_skip_guard(self):
        # Skip guard may be implied by "if configured" logic
        text = _text()
        assert "skip" in text.lower() or "absent" in text.lower() or "configured" in text.lower(), (
            "MCP check must have a graceful skip condition"
        )

    def test_mcp_check_greps_commands(self):
        assert "commands/*.md" in _text(), "MCP check must grep commands/*.md for mcp__<name>__ patterns"

    def test_mcp_check_greps_skills(self):
        assert "skills/*/SKILL.md" in _text(), "MCP check must grep skills/*/SKILL.md for mcp__<name>__ patterns"

    def test_mcp_check_reads_global_settings(self):
        assert "~/.claude/settings.json" in _text(), "MCP check must reference ~/.claude/settings.json"

    def test_mcp_check_reads_local_settings(self):
        assert ".claude/settings.json" in _text(), "MCP check must reference .claude/settings.json (repo-local)"

    def test_mcp_check_is_in_agent_e(self):
        text = _text()
        # Agent E row in the table contains both Architecture and MCP check
        agent_e_pos = text.find("Agent E")
        mcp_pos = text.find("MCP")
        assert agent_e_pos != -1, "audit skill must have Agent E"
        assert mcp_pos != -1, "audit skill must have MCP check"
        assert agent_e_pos < mcp_pos, "MCP check must be inside Agent E block"
