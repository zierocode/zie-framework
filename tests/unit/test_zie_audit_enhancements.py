from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def read_audit() -> str:
    return (COMMANDS_DIR / "audit.md").read_text()


class TestPhase1ResearchProfile:
    def test_phase1_reads_manifests(self):
        text = read_audit()
        assert "package.json" in text or "pyproject.toml" in text or "go.mod" in text, \
            "Phase 1 must read project manifests"

    def test_phase1_collects_stack(self):
        text = read_audit()
        assert "stack" in text or "languages" in text, \
            "Phase 1 must identify stack/languages"

    def test_phase1_collects_deps(self):
        text = read_audit()
        assert "deps" in text or "dependencies" in text.lower(), \
            "Phase 1 must identify dependencies"

    def test_phase1_identifies_domain(self):
        text = read_audit()
        assert "domain" in text or "app type" in text.lower(), \
            "Phase 1 must identify domain/app type"


class TestPhase2DimensionAgents:
    def test_security_agent_present(self):
        text = read_audit()
        assert "Security" in text, "Phase 2 must have Security agent"

    def test_code_health_agent_present(self):
        text = read_audit()
        assert "Code Health" in text or "Quality" in text, \
            "Phase 2 must have Code Health agent"

    def test_structural_agent_present(self):
        text = read_audit()
        assert "Structural" in text or "Architecture" in text, \
            "Phase 2 must have Structural agent"

    def test_websearch_per_agent(self):
        text = read_audit()
        assert "WebSearch" in text, "Dimension agents must use WebSearch"

    def test_agents_run_simultaneously(self):
        text = read_audit()
        assert "simultaneously" in text.lower() or "parallel" in text.lower(), \
            "Phase 2 agents must run in parallel/simultaneously"


class TestPhase3Synthesis:
    def test_synthesis_agent_present(self):
        text = read_audit()
        assert "Synthesis" in text or "synthesis" in text, \
            "Phase 3 must have a synthesis agent"

    def test_synthesis_deduplicates(self):
        text = read_audit()
        assert "Deduplicate" in text or "deduplicate" in text, \
            "Synthesis must deduplicate findings"

    def test_synthesis_ranks(self):
        text = read_audit()
        assert "Rank" in text or "rank" in text or "score" in text.lower(), \
            "Synthesis must rank/score findings"

    def test_synthesis_no_websearch(self):
        text = read_audit()
        assert "no WebSearch" in text or "0 WebSearch" in text, \
            "Synthesis agent must not use WebSearch"


class TestPhase4BacklogIntegration:
    def test_backlog_integration(self):
        text = read_audit()
        assert "backlog" in text.lower(), "Phase 4 must integrate with backlog"

    def test_roadmap_update(self):
        text = read_audit()
        assert "ROADMAP" in text, "Phase 4 must update ROADMAP"

    def test_asks_user_before_adding(self):
        text = read_audit()
        assert "yes" in text.lower() or "skip" in text.lower(), \
            "Phase 4 must ask user before adding to backlog"
