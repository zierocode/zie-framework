"""Tests for .claude-plugin/.mcp.json MCP bundle spec."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
MCP_JSON = REPO_ROOT / ".claude-plugin" / ".mcp.json"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"
COMMANDS_DIR = REPO_ROOT / "commands"
SKILLS_DIR = REPO_ROOT / "skills"
README = REPO_ROOT / "README.md"

# Files that must reference mcp__ tool names in their zie_memory branches
COMMANDS_WITH_MEMORY = [
    "backlog.md",
    "spec.md",
    "plan.md",
    "implement.md",
    "fix.md",
    "release.md",
    "retro.md",
    "init.md",
]

SKILLS_WITH_MEMORY = [
    "spec-design/SKILL.md",
    "write-plan/SKILL.md",
    "debug/SKILL.md",
]

MCP_RECALL = "mcp__plugin_zie-memory_zie-memory__recall"
MCP_REMEMBER = "mcp__plugin_zie-memory_zie-memory__remember"
MCP_DOWNVOTE = "mcp__plugin_zie-memory_zie-memory__downvote_memory"


class TestMcpJsonSchema:
    def test_file_exists(self):
        assert MCP_JSON.exists(), f".mcp.json not found at {MCP_JSON}"

    def test_parses_as_valid_json(self):
        data = json.loads(MCP_JSON.read_text())
        assert isinstance(data, dict)

    def test_top_level_key_is_mcp_servers(self):
        data = json.loads(MCP_JSON.read_text())
        assert "mcpServers" in data, f"Expected 'mcpServers' key, got: {list(data.keys())}"

    def test_zie_memory_entry_exists(self):
        data = json.loads(MCP_JSON.read_text())
        assert "zie-memory" in data["mcpServers"], (
            f"Expected 'zie-memory' server entry, got: {list(data['mcpServers'].keys())}"
        )

    def test_zie_memory_has_required_keys(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        for key in ("type", "command", "env"):
            assert key in entry, f"Missing required key '{key}' in zie-memory entry"

    def test_zie_memory_type_is_stdio(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert entry["type"] == "stdio", f"Expected type='stdio', got '{entry['type']}'"

    def test_zie_memory_command_is_npx(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert entry["command"] == "npx", f"Expected command='npx', got '{entry['command']}'"

    def test_zie_memory_args_contains_zie_memory(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert "args" in entry and "zie-memory" in entry["args"], (
            f"Expected 'zie-memory' in args, got: {entry.get('args')}"
        )


class TestMcpJsonEnvVars:
    def test_env_declares_api_url(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert "ZIE_MEMORY_API_URL" in entry["env"], (
            "ZIE_MEMORY_API_URL must be declared in zie-memory env map"
        )

    def test_env_declares_api_key(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert "ZIE_MEMORY_API_KEY" in entry["env"], (
            "ZIE_MEMORY_API_KEY must be declared in zie-memory env map"
        )

    def test_env_values_are_shell_variable_references(self):
        """Values should be ${VAR} references, not hardcoded strings."""
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        for var in ("ZIE_MEMORY_API_URL", "ZIE_MEMORY_API_KEY"):
            val = entry["env"][var]
            assert val.startswith("${") and val.endswith("}"), (
                f"env.{var} should be a shell reference like '${{VAR}}', got: '{val}'"
            )


class TestPluginJsonUnaffected:
    def test_plugin_json_still_parses(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert isinstance(data, dict)

    def test_plugin_json_has_name(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert "name" in data and data["name"] == "zie-framework"

    def test_plugin_json_has_version(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert "version" in data


class TestMcpToolNamesInCommandsAndSkills:
    def _read(self, rel_path: str) -> str:
        return (REPO_ROOT / rel_path).read_text()

    def test_zie_backlog_recall(self):
        assert MCP_RECALL in self._read("commands/backlog.md")

    def test_zie_backlog_remember(self):
        assert MCP_REMEMBER in self._read("commands/backlog.md")

    def test_zie_spec_recall(self):
        assert MCP_RECALL in self._read("commands/spec.md")

    def test_zie_plan_recall(self):
        assert MCP_RECALL in self._read("commands/plan.md")

    def test_zie_plan_remember(self):
        assert MCP_REMEMBER in self._read("commands/plan.md")

    def test_zie_implement_recall(self):
        assert MCP_RECALL in self._read("commands/implement.md")

    def test_zie_implement_remember(self):
        assert MCP_REMEMBER in self._read("commands/implement.md")

    def test_zie_fix_recall(self):
        assert MCP_RECALL in self._read("commands/fix.md")

    def test_zie_fix_remember(self):
        assert MCP_REMEMBER in self._read("commands/fix.md")

    def test_zie_release_recall(self):
        assert MCP_RECALL in self._read("commands/release.md")

    def test_zie_release_remember(self):
        assert MCP_REMEMBER in self._read("commands/release.md")

    def test_zie_retro_recall(self):
        assert MCP_RECALL in self._read("commands/retro.md")

    def test_zie_retro_remember(self):
        assert MCP_REMEMBER in self._read("commands/retro.md")

    def test_zie_retro_downvote(self):
        assert MCP_DOWNVOTE in self._read("commands/retro.md")

    def test_zie_init_remember(self):
        assert MCP_REMEMBER in self._read("commands/init.md")

    def test_skill_spec_design_recall(self):
        assert MCP_RECALL in self._read("skills/spec-design/SKILL.md")

    def test_skill_spec_design_remember(self):
        assert MCP_REMEMBER in self._read("skills/spec-design/SKILL.md")

    def test_skill_write_plan_recall(self):
        assert MCP_RECALL in self._read("skills/write-plan/SKILL.md")

    def test_skill_debug_recall(self):
        assert MCP_RECALL in self._read("skills/debug/SKILL.md")

    def test_skill_debug_remember(self):
        assert MCP_REMEMBER in self._read("skills/debug/SKILL.md")

    def test_zie_memory_enabled_guard_preserved_in_commands(self):
        """The zie_memory_enabled=true condition guard must still appear in each command."""
        for rel in COMMANDS_WITH_MEMORY:
            content = self._read(f"commands/{rel}")
            assert "zie_memory_enabled" in content, (
                f"commands/{rel} lost its zie_memory_enabled guard"
            )

    def test_zie_memory_enabled_guard_preserved_in_skills(self):
        for rel in SKILLS_WITH_MEMORY:
            content = self._read(f"skills/{rel}")
            assert "zie_memory_enabled" in content, (
                f"skills/{rel} lost its zie_memory_enabled guard"
            )


class TestReadmeBrainIntegrationSection:
    def _readme(self) -> str:
        return README.read_text()

    def test_brain_integration_section_exists(self):
        assert "## Brain Integration" in self._readme(), (
            "README.md must contain a '## Brain Integration' section"
        )

    def test_section_mentions_mcp_json(self):
        assert ".mcp.json" in self._readme(), (
            "Brain Integration section must reference .mcp.json"
        )

    def test_section_mentions_zero_setup(self):
        content = self._readme()
        assert "zero-setup" in content or "zero setup" in content, (
            "Brain Integration section must mention zero-setup"
        )

    def test_section_mentions_zie_memory_api_url(self):
        assert "ZIE_MEMORY_API_URL" in self._readme(), (
            "Brain Integration section must reference ZIE_MEMORY_API_URL"
        )

    def test_dependencies_table_updated(self):
        content = self._readme()
        assert "zie-memory" in content and "plugin" in content, (
            "Dependencies table must still reference zie-memory plugin"
        )
