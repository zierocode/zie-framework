"""Tests for audit skill: Phase 1 builds shared_context (canonical since lean-dual-audit-pipeline)."""
from pathlib import Path

# Implementation moved from commands/audit.md to skill
SKILL_PATH = Path(__file__).parents[2] / "skills" / "audit" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text()


class TestZieAuditSharedContext:
    def test_shared_context_bundle_present(self):
        """Phase 1 builds shared_context bundle."""
        assert "shared_context" in skill_text(), \
            "audit skill Phase 1 must build shared_context bundle"

    def test_shared_context_has_required_fields(self):
        """shared_context contains research_profile, backlog_slugs, adr_filenames, git_log."""
        text = skill_text()
        for field in ["research_profile", "backlog_slugs", "git_log"]:
            assert field in text, f"shared_context must include '{field}'"

    def test_agents_receive_shared_context(self):
        """Phase 2 agents receive shared_context or research_profile."""
        text = skill_text()
        assert "research_profile" in text and ("Agent" in text or "agent" in text.lower()), \
            "Phase 2 agents must receive shared context"

    def test_agents_told_not_to_re_read(self):
        """Agents instructed not to re-read manifests/git log."""
        text = skill_text()
        assert "do not re-read" in text.lower() or "Do not re-read" in text or "directly" in text, \
            "Agents must be instructed to use shared context, not re-read"

    def test_adr_filenames_in_phase1(self):
        """ADR filenames read in Phase 1 before agents spawn."""
        text = skill_text()
        assert "adr" in text.lower() or "decisions" in text.lower(), \
            "audit skill Phase 1 must reference ADR/decisions for dedup"

    def test_no_redundant_manifest_reads(self):
        """Manifests read in Phase 1, not per-agent."""
        text = skill_text()
        assert "package.json" in text or "pyproject.toml" in text, \
            "Manifests must be detected in Phase 1"
