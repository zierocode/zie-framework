"""Tests for improved /audit — v2 design."""
from pathlib import Path

AUDIT = Path(__file__).parents[2] / "commands" / "audit.md"


def read_audit() -> str:
    return AUDIT.read_text()


def _phase_text(n: int) -> str:
    text = read_audit()
    header = f"## Phase {n}"
    next_header = f"## Phase {n + 1}"
    start = text.index(header)
    try:
        end = text.index(next_header, start)
    except ValueError:
        end = len(text)
    return text[start:end]


class TestPhase1ContextBundle:
    def test_reads_roadmap_for_dedup(self):
        assert "ROADMAP" in _phase_text(1), \
            "Phase 1 must read ROADMAP to skip already-backlogged findings"

    def test_reads_adr_slugs_for_dedup(self):
        p1 = _phase_text(1)
        assert "decisions" in p1.lower() or "adr" in p1.lower(), \
            "Phase 1 must read ADR slugs to skip intentional decisions"

    def test_reads_git_log_for_focus(self):
        p1 = _phase_text(1)
        assert "git log" in p1.lower() or "recent" in p1.lower(), \
            "Phase 1 must read git log to focus audit on recent changes"

    def test_manifest_detection_is_generic(self):
        p1 = _phase_text(1)
        # Must support multiple ecosystems
        manifests = ["package.json", "pyproject.toml", "go.mod"]
        found = sum(1 for m in manifests if m in p1)
        assert found >= 2, \
            "Phase 1 must detect manifests from multiple ecosystems (generic)"


class TestPhase2ExternalResearch:
    def test_external_research_agent_present(self):
        p2 = _phase_text(2)
        assert "external research" in p2.lower() or "External Research" in p2, \
            "Phase 2 must have a dedicated External Research agent"

    def test_external_research_uses_websearch(self):
        p2 = _phase_text(2)
        assert "WebSearch" in p2, \
            "External Research agent must use WebSearch"

    def test_external_research_stack_driven(self):
        p2 = _phase_text(2)
        p2_lower = p2.lower()
        assert "stack" in p2_lower or "best practice" in p2_lower or "ecosystem" in p2_lower, \
            "External Research must be driven by detected stack/domain, not hardcoded"

    def test_external_research_improvement_framing(self):
        p2 = _phase_text(2)
        p2_lower = p2.lower()
        assert "improve" in p2_lower or "missing" in p2_lower or "should have" in p2_lower, \
            "External Research must frame findings as improvements, not just bugs"

    def test_has_four_parallel_agents(self):
        p2 = _phase_text(2)
        # Should have Agent 1, 2, 3, 4
        assert "Agent 4" in p2 or "agent 4" in p2.lower(), \
            "Phase 2 must dispatch 4 agents in parallel"


class TestPhase2DimensionConsolidation:
    def test_dependency_health_covered(self):
        p2 = _phase_text(2)
        p2_lower = p2.lower()
        assert "depend" in p2_lower or "outdated" in p2_lower or "license" in p2_lower, \
            "Phase 2 must cover Dependency Health"

    def test_performance_dimension_covered(self):
        p2 = _phase_text(2)
        p2_lower = p2.lower()
        assert "performance" in p2_lower or "n+1" in p2_lower or "blocking" in p2_lower, \
            "Phase 2 must cover Performance"

    def test_observability_dimension_covered(self):
        p2 = _phase_text(2)
        p2_lower = p2.lower()
        assert "observability" in p2_lower or "health check" in p2_lower or "metric" in p2_lower, \
            "Phase 2 must cover Observability"


class TestPhase3InlineSynthesis:
    def test_synthesis_filters_existing_backlog(self):
        p3 = _phase_text(3)
        p3_lower = p3.lower()
        assert "backlog" in p3_lower or "already" in p3_lower or "skip" in p3_lower or "filter" in p3_lower, \
            "Phase 3 must filter findings already in backlog"

    def test_synthesis_has_quick_win_category(self):
        p3 = _phase_text(3)
        assert "Quick Win" in p3 or "quick win" in p3.lower(), \
            "Phase 3 scoring must identify Quick Wins (high impact, low effort)"

    def test_synthesis_no_websearch(self):
        p3 = _phase_text(3)
        assert "no WebSearch" in p3 or "0 WebSearch" in p3, \
            "Phase 3 must not use WebSearch (synthesis only)"


class TestPhase4BatchBacklog:
    def test_batch_prompt_not_one_by_one(self):
        p4 = _phase_text(4)
        p4_lower = p4.lower()
        assert "all" in p4_lower or "batch" in p4_lower, \
            "Phase 4 must offer batch backlog addition, not one-by-one"

    def test_critical_and_high_offered(self):
        p4 = _phase_text(4)
        assert "CRITICAL" in p4 and "HIGH" in p4, \
            "Phase 4 must surface both CRITICAL and HIGH findings for backlog"


class TestGenericApplicability:
    def test_no_python_specific_assumptions(self):
        text = read_audit()
        # Should not hardcode Python-only patterns as the only option
        assert "package.json" in text or "go.mod" in text, \
            "Audit must support non-Python projects"

    def test_stack_variable_drives_research(self):
        text = read_audit()
        # Research should reference detected stack, not hardcoded language
        assert "{stack}" in text or "detected stack" in text.lower() or "stack" in text, \
            "External research must be driven by detected stack variable"

    def test_domain_variable_drives_research(self):
        text = read_audit()
        assert "{domain}" in text or "detected domain" in text.lower() or "domain" in text, \
            "External research must be driven by detected domain variable"
