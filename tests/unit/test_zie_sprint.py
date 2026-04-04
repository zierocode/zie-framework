"""Tests for /zie-sprint command contract."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "zie-sprint.md"


def _text():
    return CMD.read_text()


class TestCommandExists:
    def test_file_exists(self):
        assert CMD.exists(), "commands/zie-sprint.md must exist"

    def test_frontmatter_has_description(self):
        assert "description:" in _text(), "must have frontmatter description"

    def test_frontmatter_has_allowed_tools(self):
        assert "allowed-tools:" in _text(), "must declare allowed-tools"

    def test_frontmatter_model_sonnet(self):
        assert "model: sonnet" in _text(), "model must be sonnet (orchestration work)"

    def test_frontmatter_effort_high(self):
        assert "effort: high" in _text(), "effort must be high (full sprint cycle)"


class TestAuditPhase:
    def test_has_audit_step(self):
        assert "AUDIT" in _text(), "must have AUDIT step to classify items"

    def test_audit_classifies_items(self):
        text = _text()
        assert "needs_spec" in text or "Needs Spec" in text, \
            "AUDIT must classify items needing spec"

    def test_audit_asks_confirmation(self):
        text = _text()
        assert "yes" in text.lower() and "cancel" in text.lower(), \
            "AUDIT must ask for confirmation before executing"

    def test_dry_run_flag(self):
        assert "--dry-run" in _text(), "must support --dry-run flag"

    def test_dependency_detection(self):
        assert "depends_on" in _text(), "AUDIT must detect depends_on annotations"


class TestPhaseStructure:
    def test_has_five_phases(self):
        text = _text()
        for n in ("1", "2", "3", "4", "5"):
            assert f"PHASE {n}" in text, f"must have PHASE {n}"

    def test_phase1_spec_parallel(self):
        text = _text()
        phase1_idx = text.index("PHASE 1")
        phase2_idx = text.index("PHASE 2")
        phase1_section = text[phase1_idx:phase2_idx]
        assert "parallel" in phase1_section.lower() or "run_in_background" in phase1_section, \
            "Phase 1 must use parallel agents for spec"

    def test_phase1_uses_skill_chain(self):
        text = _text()
        assert "spec-reviewer" in text and "write-plan" in text and "plan-reviewer" in text, \
            "Phase 1 must use skill chain (spec-reviewer, write-plan, plan-reviewer)"

    def test_phase3_sequential_wip1(self):
        text = _text()
        phase3_idx = text.index("PHASE 3")
        phase4_idx = text.index("PHASE 4")
        phase3_section = text[phase3_idx:phase4_idx]
        assert "sequential" in phase3_section.lower() or "WIP=1" in phase3_section, \
            "Phase 3 must be sequential (WIP=1)"

    def test_phase4_batch_release(self):
        text = _text()
        phase4_idx = text.index("PHASE 4")
        phase5_idx = text.index("PHASE 5")
        phase4_section = text[phase4_idx:phase5_idx]
        assert "release" in phase4_section.lower(), \
            "Phase 4 must invoke release"

    def test_phase5_retro(self):
        text = _text()
        phase5_idx = text.index("PHASE 5")
        phase5_section = text[phase5_idx:]
        assert "retro" in phase5_section.lower(), \
            "Phase 5 must invoke retro"


class TestContextBundle:
    def test_context_bundle_loaded_once(self):
        text = _text()
        assert "context_bundle" in text, \
            "must load context_bundle once and pass to all downstream agents"

    def test_context_bundle_referenced_in_phase1(self):
        text = _text()
        phase1_idx = text.index("PHASE 1")
        phase2_idx = text.index("PHASE 2")
        phase1_section = text[phase1_idx:phase2_idx]
        assert "context_bundle" in phase1_section, \
            "context_bundle must be referenced in PHASE 1 agent spawning"

    def test_context_bundle_loaded_once(self):
        text = _text()
        # context_bundle is loaded once before phases, not re-referenced in each phase
        assert "context_bundle" in text, \
            "context_bundle must be loaded (once) in the Load Context Bundle section"

    def test_adrs_loaded(self):
        assert "decisions" in _text(), \
            "context bundle must load decisions/*.md (ADRs)"

    def test_context_md_loaded(self):
        assert "context.md" in _text(), \
            "context bundle must load project/context.md"


class TestArgumentParsing:
    def test_skip_ready_flag(self):
        assert "--skip-ready" in _text(), "must support --skip-ready flag"

    def test_version_override_flag(self):
        assert "--version=" in _text(), "must support --version=X.Y.Z flag"

    def test_slug_filtering(self):
        text = _text()
        assert "slugs" in text or "slug" in text.lower(), \
            "must support filtering by specific slugs"


class TestErrorHandling:
    def test_empty_backlog_handling(self):
        text = _text()
        assert "empty" in text.lower() or "Nothing" in text, \
            "must handle empty backlog gracefully"

    def test_wip_active_handling(self):
        text = _text()
        assert "WIP" in text or "active" in text.lower(), \
            "must warn when WIP item is active"

    def test_phase_failure_halts(self):
        text = _text()
        assert "halt" in text.lower() or "STOP" in text or "stop" in text.lower(), \
            "phase failure must halt sprint"

    def test_phase5_retro_non_blocking(self):
        text = _text()
        assert "non-blocking" in text.lower() or "Non-blocking" in text, \
            "Phase 5 retro failure must be non-blocking"


class TestSummaryOutput:
    def test_has_summary_section(self):
        assert "SPRINT COMPLETE" in _text() or "Summary" in _text(), \
            "must print sprint summary on completion"

    def test_summary_shows_shipped_count(self):
        text = _text()
        assert "Shipped" in text, "summary must show how many items were shipped"
