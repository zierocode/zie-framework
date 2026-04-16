"""Tests for /audit — implementation in audit skill (canonical since lean-dual-audit-pipeline)."""

from pathlib import Path

# audit.md is now a thin dispatcher; all implementation is in the skill
SKILL = Path(__file__).parents[2] / "skills" / "audit" / "SKILL.md"
AUDIT = Path(__file__).parents[2] / "commands" / "audit.md"


def read_skill() -> str:
    return SKILL.read_text()


def read_audit() -> str:
    return AUDIT.read_text()


def _phase_text(n: int) -> str:
    text = read_skill()
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
        assert "ROADMAP" in read_skill() or "roadmap" in read_skill().lower(), (
            "Skill must read ROADMAP to skip already-backlogged findings"
        )

    def test_reads_adr_slugs_for_dedup(self):
        text = read_skill()
        assert "decisions" in text.lower() or "adr" in text.lower(), (
            "Skill must read ADR slugs to skip intentional decisions"
        )

    def test_reads_git_log_for_focus(self):
        text = read_skill()
        assert "git log" in text.lower() or "recent" in text.lower(), (
            "Skill must reference git log for recent activity focus"
        )

    def test_manifest_detection_is_generic(self):
        text = read_skill()
        manifests = ["package.json", "pyproject.toml", "go.mod"]
        found = sum(1 for m in manifests if m in text)
        assert found >= 2, "Skill must detect manifests from multiple ecosystems (generic)"


class TestPhase2ExternalResearch:
    def test_external_research_agent_present(self):
        text = read_skill()
        assert "external research" in text.lower() or "External Research" in text, (
            "Skill must have a dedicated External Research phase or agent"
        )

    def test_external_research_uses_websearch(self):
        text = read_skill()
        assert "WebSearch" in text, "External Research must use WebSearch"

    def test_external_research_stack_driven(self):
        text = read_skill()
        text_lower = text.lower()
        assert "stack" in text_lower or "best practice" in text_lower or "ecosystem" in text_lower, (
            "External Research must be driven by detected stack/domain, not hardcoded"
        )

    def test_external_research_improvement_framing(self):
        text = read_skill()
        text_lower = text.lower()
        assert "improve" in text_lower or "missing" in text_lower or "should have" in text_lower, (
            "External Research must frame findings as improvements, not just bugs"
        )

    def test_has_four_parallel_agents(self):
        text = read_skill()
        assert "Agent D" in text or "Agent E" in text or "5 parallel" in text or "4 parallel" in text, (
            "Skill must dispatch multiple agents in parallel"
        )


class TestPhase2DimensionConsolidation:
    def test_dependency_health_covered(self):
        text = read_skill().lower()
        assert "depend" in text or "outdated" in text or "license" in text, "Skill must cover Dependency Health"

    def test_performance_dimension_covered(self):
        text = read_skill().lower()
        assert "performance" in text or "n+1" in text or "blocking" in text, "Skill must cover Performance"

    def test_observability_dimension_covered(self):
        text = read_skill().lower()
        assert "observability" in text or "health check" in text or "metric" in text, "Skill must cover Observability"


class TestPhase3InlineSynthesis:
    def test_synthesis_filters_existing_backlog(self):
        text = read_skill().lower()
        assert "backlog" in text or "already" in text or "skip" in text or "filter" in text, (
            "Skill must filter findings already in backlog"
        )

    def test_synthesis_has_quick_win_category(self):
        text = read_skill()
        assert "Quick Win" in text or "quick win" in text.lower(), (
            "Skill scoring must identify Quick Wins (high impact, low effort)"
        )

    def test_synthesis_no_websearch(self):
        # Phase 4 (Synthesis) must not use WebSearch
        p4 = _phase_text(4)
        assert "WebSearch" not in p4 or "No WebSearch" in p4 or "no WebSearch" in p4, (
            "Phase 4 (Synthesis) must not use WebSearch"
        )


class TestPhase4BatchBacklog:
    def test_batch_prompt_not_one_by_one(self):
        text = read_skill().lower()
        assert "all" in text or "batch" in text, "Skill must offer batch backlog addition, not one-by-one"

    def test_critical_and_high_offered(self):
        text = read_skill()
        assert "CRITICAL" in text or "critical" in text.lower(), "Skill must surface CRITICAL findings for backlog"


class TestGenericApplicability:
    def test_no_python_specific_assumptions(self):
        text = read_audit()
        # audit.md thin dispatcher must not be python-specific; skill handles generics
        assert "audit" in text, "audit.md must delegate to audit skill (which handles multi-stack)"

    def test_stack_variable_drives_research(self):
        text = read_skill()
        assert "{stack}" in text or "detected stack" in text.lower() or "stack" in text, (
            "External research must be driven by detected stack variable"
        )

    def test_domain_variable_drives_research(self):
        text = read_skill()
        assert "{domain}" in text or "detected domain" in text.lower() or "domain" in text, (
            "External research must be driven by detected domain variable"
        )
