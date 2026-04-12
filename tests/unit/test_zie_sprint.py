"""Tests for /sprint command contract."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD = REPO_ROOT / "commands" / "sprint.md"


def _text():
    return CMD.read_text()


class TestCommandExists:
    def test_file_exists(self):
        assert CMD.exists(), "commands/sprint.md must exist"

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
    def test_has_four_phases(self):
        text = _text()
        for n in ("1", "2", "3", "4"):
            assert f"PHASE {n}" in text, f"must have PHASE {n}"

    def test_no_standalone_phase2_plan(self):
        text = _text()
        # Phase 2 is now IMPLEMENT — planning is inlined in Phase 1
        phase2_idx = text.index("PHASE 2")
        phase3_idx = text.index("PHASE 3")
        phase2_section = text[phase2_idx:phase3_idx]
        assert "IMPLEMENT" in phase2_section or "sequential" in phase2_section.lower(), \
            "Phase 2 must be IMPLEMENT (not a standalone plan phase)"

    def test_phase1_spec_parallel(self):
        text = _text()
        phase1_idx = text.index("PHASE 1")
        phase2_idx = text.index("PHASE 2")
        phase1_section = text[phase1_idx:phase2_idx]
        assert "parallel" in phase1_section.lower() or "run_in_background" in phase1_section, \
            "Phase 1 must use parallel agents for spec"

    def test_phase1_has_inline_retry(self):
        text = _text()
        phase1_idx = text.index("PHASE 1")
        phase2_idx = text.index("PHASE 2")
        phase1_section = text[phase1_idx:phase2_idx]
        assert "retry" in phase1_section.lower() or "inline retry" in phase1_section.lower(), \
            "Phase 1 must have inline retry for partial failures (no separate Phase 2 plan)"

    def test_phase1_uses_skill_chain(self):
        text = _text()
        assert "spec-reviewer" in text and "write-plan" in text and "plan-reviewer" in text, \
            "Phase 1 must use skill chain (spec-reviewer, write-plan, plan-reviewer)"

    def test_phase2_sequential_wip1(self):
        text = _text()
        phase2_idx = text.index("PHASE 2")
        phase3_idx = text.index("PHASE 3")
        phase2_section = text[phase2_idx:phase3_idx]
        assert "sequential" in phase2_section.lower() or "WIP=1" in phase2_section, \
            "Phase 2 must be sequential (WIP=1)"

    def test_phase3_batch_release(self):
        text = _text()
        phase3_idx = text.index("PHASE 3")
        phase4_idx = text.index("PHASE 4")
        phase3_section = text[phase3_idx:phase4_idx]
        assert "release" in phase3_section.lower(), \
            "Phase 3 must invoke release"

    def test_phase4_retro(self):
        text = _text()
        phase4_idx = text.index("PHASE 4")
        phase4_section = text[phase4_idx:]
        assert "retro" in phase4_section.lower(), \
            "Phase 4 must invoke retro"


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

    def test_phase4_retro_non_blocking(self):
        text = _text()
        assert "non-blocking" in text.lower() or "Non-blocking" in text, \
            "Phase 4 retro failure must be non-blocking"


class TestSummaryOutput:
    def test_has_summary_section(self):
        assert "SPRINT COMPLETE" in _text() or "Summary" in _text(), \
            "must print sprint summary on completion"

    def test_summary_shows_shipped_count(self):
        text = _text()
        assert "Shipped" in text, "summary must show how many items were shipped"


class TestPhase2ImplementAgent:
    def test_phase2_uses_zie_implement_make_target(self):
        """Phase 2 must invoke make zie-implement (agent mode), not a non-existent Skill."""
        t = _text()
        phase2_idx = t.index("PHASE 2")
        phase3_idx = t.index("PHASE 3")
        phase2 = t[phase2_idx:phase3_idx]
        assert "zie-implement" in phase2, \
            "Sprint Phase 2 must call make zie-implement (agent mode via Bash)"

    def test_phase2_no_skill_zie_implement(self):
        """Phase 2 must NOT call Skill(zie-framework:zie-implement) — that skill does not exist."""
        t = _text()
        phase2_idx = t.index("PHASE 2")
        phase3_idx = t.index("PHASE 3")
        phase2 = t[phase2_idx:phase3_idx]
        assert "Skill(zie-framework:zie-implement" not in phase2, \
            "Sprint Phase 2 must not call non-existent Skill zie-implement — use make zie-implement"

    def test_phase2_checks_roadmap_after_implement(self):
        """Phase 2 must verify ROADMAP state after implement completes."""
        t = _text()
        phase2_idx = t.index("PHASE 2")
        phase3_idx = t.index("PHASE 3")
        phase2 = t[phase2_idx:phase3_idx]
        assert "ROADMAP" in phase2, \
            "Phase 2 must check ROADMAP.md after implement to confirm success"


class TestAllItemsEnforcement:
    def test_no_silent_drops(self):
        text = _text()
        assert "silent" in text.lower() or "No item may" in text or "must be included" in text, \
            "must explicitly forbid silently dropping items from sprint"

    def test_all_means_all_language(self):
        text = _text()
        assert "ALL" in text or "all" in text.lower(), \
            "must state that all items means every item"

    def test_consolidation_requires_declaration(self):
        text = _text()
        assert "MERGED" in text or "merged" in text.lower() or "consolid" in text.lower(), \
            "item consolidation must be declared to user (not silent)"

    def test_consolidation_explains_original_items(self):
        text = _text()
        assert "Original items" in text or "original item" in text.lower(), \
            "merged backlog must reference original items by name"

    def test_consolidation_conditions_listed(self):
        text = _text()
        assert "trivial" in text.lower() or "15 min" in text or "small" in text.lower(), \
            "must define conditions under which consolidation is allowed"
