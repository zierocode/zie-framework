"""Tests for audit skill — implementation canonical since lean-dual-audit-pipeline."""

from pathlib import Path

SKILL = Path(__file__).parents[2] / "skills" / "audit" / "SKILL.md"


def read_skill() -> str:
    return SKILL.read_text()


class TestPhase1ResearchProfile:
    def test_phase1_reads_manifests(self):
        text = read_skill()
        assert "package.json" in text or "pyproject.toml" in text or "go.mod" in text, (
            "Phase 1 must read project manifests"
        )

    def test_phase1_collects_stack(self):
        text = read_skill()
        assert "stack" in text or "languages" in text, "Phase 1 must identify stack/languages"

    def test_phase1_collects_deps(self):
        text = read_skill()
        assert "deps" in text or "dependencies" in text.lower(), "Phase 1 must identify dependencies"

    def test_phase1_identifies_domain(self):
        text = read_skill()
        assert "domain" in text or "app type" in text.lower(), "Phase 1 must identify domain/app type"


class TestPhase2DimensionAgents:
    def test_security_agent_present(self):
        text = read_skill()
        assert "Security" in text, "Phase 2 must have Security agent"

    def test_code_health_agent_present(self):
        text = read_skill()
        assert "Code Health" in text or "Quality" in text or "Lean" in text, (
            "Phase 2 must have Code Health/Quality agent"
        )

    def test_structural_agent_present(self):
        text = read_skill()
        assert "Structural" in text or "Architecture" in text, "Phase 2 must have Structural/Architecture agent"

    def test_websearch_per_agent(self):
        text = read_skill()
        assert "WebSearch" in text, "Dimension agents must use WebSearch"

    def test_agents_run_simultaneously(self):
        text = read_skill()
        assert "simultaneously" in text.lower() or "parallel" in text.lower(), (
            "Phase 2 agents must run in parallel/simultaneously"
        )


class TestPhase3Synthesis:
    def test_synthesis_agent_present(self):
        text = read_skill()
        assert "Synthesis" in text or "synthesis" in text, "Skill must have a synthesis phase"

    def test_synthesis_deduplicates(self):
        text = read_skill()
        assert "Deduplicate" in text or "deduplicate" in text or "Dedup" in text, "Synthesis must deduplicate findings"

    def test_synthesis_ranks(self):
        text = read_skill()
        assert "Rank" in text or "rank" in text or "score" in text.lower(), "Synthesis must rank/score findings"

    def test_synthesis_no_websearch(self):
        text = read_skill()
        assert "No WebSearch" in text or "no WebSearch" in text or "0 WebSearch" in text, (
            "Synthesis phase must not use WebSearch"
        )


class TestPhase4BacklogIntegration:
    def test_backlog_integration(self):
        text = read_skill()
        assert "backlog" in text.lower(), "Skill must integrate with backlog"

    def test_roadmap_update(self):
        text = read_skill()
        assert "ROADMAP" in text, "Skill must update ROADMAP"

    def test_asks_user_before_adding(self):
        text = read_skill()
        assert "yes" in text.lower() or "skip" in text.lower(), "Skill must ask user before adding to backlog"
