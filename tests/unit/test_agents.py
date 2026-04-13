"""
Structural tests for session-wide agent definition files.
Verifies frontmatter keys, system prompt content, and safety contracts.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
AGENTS_DIR = REPO_ROOT / "agents"


def parse_agent_file(name: str) -> tuple[dict, str]:
    """Parse an agent .md file into (frontmatter_dict, body_str).

    Frontmatter is the YAML block between the first --- delimiters.
    Body is everything after the closing ---.
    """
    path = AGENTS_DIR / name
    content = path.read_text()
    parts = content.split("---")
    # parts[0] == "" (before opening ---), parts[1] == YAML, parts[2+] == body
    assert len(parts) >= 3, (
        f"{name}: could not parse frontmatter (need at least 2 --- delimiters)"
    )
    fm_raw = parts[1].strip()
    body = "---".join(parts[2:]).strip()
    fm: dict = {}
    for line in fm_raw.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, body


class TestImplementModeAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "zie-implement-mode.md").exists(), \
            "agents/implement-mode.md not found"

    def test_frontmatter_model(self):
        fm, _ = parse_agent_file("zie-implement-mode.md")
        assert fm.get("model", "").split("#")[0].strip() == "sonnet", \
            f"Expected model: sonnet, got: {fm.get('model')}"

    def test_frontmatter_permission_mode(self):
        fm, _ = parse_agent_file("zie-implement-mode.md")
        assert fm.get("permissionMode") == "acceptEdits", \
            f"Expected permissionMode: acceptEdits, got: {fm.get('permissionMode')}"

    def test_frontmatter_tools_all(self):
        fm, _ = parse_agent_file("zie-implement-mode.md")
        assert fm.get("tools") == "all", \
            f"Expected tools: all, got: {fm.get('tools')}"

    def test_body_mentions_tdd_loop_skill(self):
        _, body = parse_agent_file("zie-implement-mode.md")
        assert "tdd-loop" in body, "System prompt must reference tdd-loop skill"

    def test_body_mentions_test_pyramid_skill(self):
        _, body = parse_agent_file("zie-implement-mode.md")
        assert "test-pyramid" in body, "System prompt must reference test-pyramid skill"

    def test_body_mentions_sdlc_pipeline_stages(self):
        _, body = parse_agent_file("zie-implement-mode.md")
        for stage in ["/backlog", "/spec", "/plan", "/implement",
                      "/release", "/retro"]:
            assert stage in body, f"System prompt must mention SDLC stage: {stage}"

    def test_body_mentions_wip_rule(self):
        _, body = parse_agent_file("zie-implement-mode.md")
        assert "WIP=1" in body or "WIP = 1" in body, \
            "System prompt must mention WIP=1 rule"

    def test_body_has_graceful_degradation_note(self):
        _, body = parse_agent_file("zie-implement-mode.md")
        assert "zie-init" in body or "/init" in body, \
            "System prompt must instruct graceful degradation when project not initialized"

    def test_no_secrets_in_file(self):
        path = AGENTS_DIR / "zie-implement-mode.md"
        content = path.read_text()
        secret_patterns = [
            r"sk-[A-Za-z0-9]{20,}",
            r"api[_-]?key\s*=\s*\S+",
            r"password\s*=\s*\S+",
            r"token\s*=\s*[A-Za-z0-9]{16,}",
        ]
        for pat in secret_patterns:
            assert not re.search(pat, content, re.IGNORECASE), \
                f"Possible secret found in zie-implement-mode.md matching pattern: {pat}"


class TestAuditModeAgent:
    def test_file_exists(self):
        assert (AGENTS_DIR / "zie-audit-mode.md").exists(), \
            "agents/audit-mode.md not found"

    def test_frontmatter_model(self):
        fm, _ = parse_agent_file("zie-audit-mode.md")
        assert fm.get("model", "").split("#")[0].strip() == "sonnet", \
            f"Expected model: sonnet, got: {fm.get('model')}"

    def test_frontmatter_no_permission_mode_restriction(self):
        """zie-audit-mode must NOT restrict permissionMode or tools — needs Agent tool for Phase 2 subagents."""
        fm, _ = parse_agent_file("zie-audit-mode.md")
        # permissionMode should be absent (removed in v1.28.4 to fix audit hang)
        assert fm.get("permissionMode") is None, \
            f"permissionMode should be absent (audit needs full tool access), got: {fm.get('permissionMode')}"

    def test_frontmatter_no_tools_restriction(self):
        """zie-audit-mode must NOT restrict tools — needs Agent tool for Phase 2 subagents."""
        fm, _ = parse_agent_file("zie-audit-mode.md")
        # tools should be absent (removed in v1.28.4 to fix audit hang)
        assert fm.get("tools") is None, \
            f"tools should be absent (audit needs full tool access), got: {fm.get('tools')}"

    def test_frontmatter_tools_excludes_write(self):
        fm, _ = parse_agent_file("zie-audit-mode.md")
        tools_val = fm.get("tools", "")
        tool_list = re.split(r"[\[\],\s]+", tools_val)
        assert "Write" not in tool_list, \
            f"Write tool must not be in audit-mode tool list: {tools_val}"

    def test_body_enforces_read_only(self):
        _, body = parse_agent_file("zie-audit-mode.md")
        assert "read-only" in body.lower() or "read only" in body.lower(), \
            "System prompt must assert read-only contract"

    def test_body_mentions_audit_mode_message(self):
        _, body = parse_agent_file("zie-audit-mode.md")
        assert "audit mode" in body.lower(), \
            "System prompt must mention 'audit mode' for user-facing messaging"

    def test_body_directs_findings_to_backlog(self):
        _, body = parse_agent_file("zie-audit-mode.md")
        assert "backlog" in body.lower(), \
            "System prompt must instruct surfacing findings as backlog candidates"

    def test_body_prohibits_writes(self):
        _, body = parse_agent_file("zie-audit-mode.md")
        assert (
            "no write" in body.lower()
            or "do not write" in body.lower()
            or "never write" in body.lower()
            or "mutation" in body.lower()
        ), "System prompt must explicitly prohibit write operations"

    def test_no_secrets_in_file(self):
        path = AGENTS_DIR / "zie-audit-mode.md"
        content = path.read_text()
        secret_patterns = [
            r"sk-[A-Za-z0-9]{20,}",
            r"api[_-]?key\s*=\s*\S+",
            r"password\s*=\s*\S+",
            r"token\s*=\s*[A-Za-z0-9]{16,}",
        ]
        for pat in secret_patterns:
            assert not re.search(pat, content, re.IGNORECASE), \
                f"Possible secret found in zie-audit-mode.md matching pattern: {pat}"


class TestPluginJsonAgentsDir:
    def test_agents_dir_key_present(self):
        plugin = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text()
        )
        assert "agentsDir" in plugin, \
            "plugin.json must contain 'agentsDir' key"

    def test_agents_dir_value(self):
        plugin = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text()
        )
        assert plugin["agentsDir"] == "agents", \
            f"Expected agentsDir: 'agents', got: {plugin.get('agentsDir')}"


class TestSettingsJson:
    def test_settings_json_exists(self):
        assert (REPO_ROOT / "settings.json").exists(), \
            "settings.json not found at plugin root"

    def test_settings_json_has_default_agent(self):
        settings = json.loads((REPO_ROOT / "settings.json").read_text())
        assert "defaultAgent" in settings, \
            "settings.json must contain 'defaultAgent' key"

    def test_settings_json_default_agent_is_implement_mode(self):
        settings = json.loads((REPO_ROOT / "settings.json").read_text())
        assert settings["defaultAgent"] == "zie-implement-mode", \
            f"Expected defaultAgent: 'zie-implement-mode', got: {settings.get('defaultAgent')}"

    def test_settings_json_has_invocation_key(self):
        settings = json.loads((REPO_ROOT / "settings.json").read_text())
        assert "invocation" in settings, \
            "settings.json must contain 'invocation' key documenting usage examples"

    def test_settings_json_is_valid_json(self):
        content = (REPO_ROOT / "settings.json").read_text()
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            pytest.fail(f"settings.json is not valid JSON: {e}")


class TestReadmeAgentDocs:
    def test_agent_modes_section_present(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "Agent Modes" in readme, \
            "README.md must contain an 'Agent Modes' section"

    def test_implement_mode_in_readme(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "zie-implement-mode" in readme, \
            "README.md must document zie-implement-mode agent"

    def test_audit_mode_in_readme(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "zie-audit-mode" in readme, \
            "README.md must document zie-audit-mode agent"

    def test_agent_invocation_command_in_readme(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "--agent" in readme, \
            "README.md must show --agent flag in invocation example"


class TestClaudeMdAgentDocs:
    def test_agent_invocation_in_claude_md(self):
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
        assert "--agent" in claude_md, \
            "CLAUDE.md must include --agent invocation example"

    def test_implement_mode_in_claude_md(self):
        claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
        assert "zie-implement-mode" in claude_md, \
            "CLAUDE.md must reference zie-implement-mode"


class TestComponentsRegistryAgents:
    def test_agents_section_present(self):
        components = (
            REPO_ROOT / "zie-framework" / "project" / "components.md"
        ).read_text()
        assert "## Agents" in components, \
            "components.md must have an '## Agents' section"

    def test_implement_mode_in_components(self):
        components = (
            REPO_ROOT / "zie-framework" / "project" / "components.md"
        ).read_text()
        assert "zie-implement-mode" in components, \
            "components.md Agents section must list zie-implement-mode"

    def test_audit_mode_in_components(self):
        components = (
            REPO_ROOT / "zie-framework" / "project" / "components.md"
        ).read_text()
        assert "zie-audit-mode" in components, \
            "components.md Agents section must list zie-audit-mode"
