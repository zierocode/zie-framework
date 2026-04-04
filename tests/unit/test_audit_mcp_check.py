"""Tests for /zie-audit MCP server usage check (audit-mcp-check feature)."""
from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "zie-audit.md"


def _text():
    return CMD.read_text()


class TestMcpCheckPresent:
    def test_mcp_check_exists(self):
        assert "MCP Server Usage" in _text(), \
            "zie-audit.md Agent 2 must contain an MCP Server Usage check"

    def test_mcp_check_has_low_finding(self):
        assert "consider removing to reduce context overhead" in _text(), \
            "MCP check must emit LOW finding with 'consider removing to reduce context overhead'"

    def test_mcp_check_has_skip_guard(self):
        assert "skip this check entirely" in _text(), \
            "MCP check must have a graceful skip condition when no mcpServers configured"

    def test_mcp_check_greps_commands(self):
        assert "commands/*.md" in _text(), \
            "MCP check must grep commands/*.md for mcp__<name>__ patterns"

    def test_mcp_check_greps_skills(self):
        assert "skills/*/SKILL.md" in _text(), \
            "MCP check must grep skills/*/SKILL.md for mcp__<name>__ patterns"

    def test_mcp_check_reads_global_settings(self):
        text = _text()
        assert "~/.claude/settings.json" in text, \
            "MCP check must read ~/.claude/settings.json"

    def test_mcp_check_reads_local_settings(self):
        text = _text()
        assert ".claude/settings.json" in text, \
            "MCP check must read .claude/settings.json (repo-local)"

    def test_mcp_check_is_in_agent2(self):
        text = _text()
        # MCP check must appear before Agent 3 (after Agent 2 starts)
        agent2_pos = text.find("Agent 2 —")
        agent3_pos = text.find("Agent 3 —")
        mcp_pos = text.find("MCP Server Usage")
        assert agent2_pos != -1 and agent3_pos != -1 and mcp_pos != -1
        assert agent2_pos < mcp_pos < agent3_pos, \
            "MCP check must be inside Agent 2 block (after Agent 2, before Agent 3)"
