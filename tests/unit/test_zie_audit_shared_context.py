"""Tests for context-lean-sprint Task 6: zie-audit Phase 1 builds shared_context."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "audit.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestZieAuditSharedContext:
    def test_shared_context_bundle_present(self):
        """Phase 1 builds shared_context bundle."""
        text = cmd_text()
        assert "shared_context" in text, \
            "zie-audit Phase 1 must build shared_context bundle"

    def test_shared_context_has_required_fields(self):
        """shared_context contains stack, domain, deps, backlog_slugs, git_log, adr_cache_path."""
        text = cmd_text()
        for field in ["stack", "domain", "deps", "backlog_slugs", "git_log", "adr_cache_path"]:
            assert field in text, f"shared_context must include '{field}'"

    def test_agents_receive_shared_context(self):
        """Phase 2 agents receive shared_context parameter."""
        text = cmd_text()
        assert "shared_context" in text and "Agent" in text, \
            "Phase 2 agents must receive shared_context"

    def test_agents_told_not_to_re_read(self):
        """Agents instructed not to re-read manifests/git log."""
        text = cmd_text()
        assert "do not re-read" in text.lower() or "Do not re-read" in text, \
            "Agents must be instructed to not re-read already-loaded context"

    def test_adr_cache_built_in_phase1(self):
        """ADR cache is built in Phase 1 before agents spawn."""
        text = cmd_text()
        assert "write_adr_cache" in text, \
            "zie-audit Phase 1 must call write_adr_cache"

    def test_no_redundant_manifest_reads(self):
        """Each manifest file read only in Phase 1, not per-agent."""
        text = cmd_text()
        # Phase 1 reads manifests once, agents get shared_context
        sections = text.split("## Phase 2")
        phase1 = sections[0]
        assert "package.json" in phase1 or "pyproject.toml" in phase1, \
            "Manifests must be read in Phase 1"
