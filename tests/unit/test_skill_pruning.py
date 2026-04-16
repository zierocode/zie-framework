from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def read_skill(skill: str) -> str:
    return (SKILLS_DIR / skill / "SKILL.md").read_text()


class TestTddLoopPruning:
    def test_cycle_time_target_section_absent(self):
        text = read_skill("tdd-loop")
        assert "## Cycle Time Target" not in text, "Cycle Time Target section must be removed"

    def test_cycle_time_prose_absent(self):
        text = read_skill("tdd-loop")
        assert "Each RED→GREEN→REFACTOR cycle should take < 15 minutes." not in text, "Cycle time prose must be removed"

    def test_stuck_15_minutes_line_absent(self):
        text = read_skill("tdd-loop")
        assert "If stuck > 15 minutes on GREEN" not in text, "Stuck-15-minutes line must be removed"

    def test_core_rules_preserved(self):
        text = read_skill("tdd-loop")
        assert "Never skip RED" in text
        assert "One failing test at a time" in text

    def test_quality_checklist_preserved(self):
        text = read_skill("tdd-loop")
        assert "## Test Quality Checklist" in text
        assert "Name describes expected behavior" in text


class TestTestPyramidPruning:
    def test_bad_good_name_examples_absent(self):
        text = read_skill("test-pyramid")
        assert "BAD: `test_hybrid_search_function`" not in text, "BAD/GOOD name examples must be removed"

    def test_bad_good_e2e_examples_absent(self):
        text = read_skill("test-pyramid")
        assert 'BAD: "test every page loads"' not in text, "BAD/GOOD E2E examples must be removed"

    def test_playwright_code_block_absent(self):
        text = read_skill("test-pyramid")
        assert "tests/e2e/fixtures.ts" not in text, "Playwright fixtures.ts example must be removed"

    def test_playwright_config_essentials_absent(self):
        text = read_skill("test-pyramid")
        assert "playwright.config.ts" not in text, "playwright.config.ts essentials section must be removed"

    def test_retries_config_example_absent(self):
        text = read_skill("test-pyramid")
        assert "`retries: 1` in CI" not in text, "retries config example must be removed"

    def test_pyramid_ascii_preserved(self):
        text = read_skill("test-pyramid")
        assert "UNIT TESTS" in text
        assert "Playwright" in text

    def test_trigger_table_preserved(self):
        text = read_skill("test-pyramid")
        assert "PostToolUse hook" in text
        assert "/release gate" in text


class TestWritePlanPruning:
    def test_future_skill_authors_note_absent(self):
        text = read_skill("write-plan")
        assert "Note for future skill authors" not in text, "Future skill authors note must be removed"

    def test_claude_skill_dir_reference_absent(self):
        text = read_skill("write-plan")
        assert "CLAUDE_SKILL_DIR" not in text, "CLAUDE_SKILL_DIR reference must be removed"

    def test_context_from_brain_section_absent(self):
        text = read_skill("write-plan")
        assert "## Context from brain" not in text, "Context from brain section must be removed"

    def test_prior_memories_prose_absent(self):
        text = read_skill("write-plan")
        assert "_Prior memories relevant to this feature are surfaced here" not in text, (
            "Prior memories stub prose must be removed"
        )

    def test_plan_header_format_preserved(self):
        text = read_skill("write-plan")
        assert "approved: false" in text
        assert "## โครงสร้าง Task" in text

    def test_reviewer_loop_not_in_skill(self):
        # Reviewer gate belongs in zie-plan.md, not in the write-plan skill
        text = read_skill("write-plan")
        assert "plan-review" not in text


class TestSpecDesignPruning:
    def test_future_skill_authors_note_absent(self):
        text = read_skill("spec-design")
        assert "Note for future skill authors" not in text, "Future skill authors note must be removed"

    def test_claude_skill_dir_reference_absent(self):
        text = read_skill("spec-design")
        assert "CLAUDE_SKILL_DIR" not in text, "CLAUDE_SKILL_DIR reference must be removed"

    def test_steps_preserved(self):
        text = read_skill("spec-design")
        assert "Understand the idea" in text
        assert "Spec reviewer loop" in text
        assert "Record approval" in text

    def test_spec_format_preserved(self):
        text = read_skill("spec-design")
        assert "**Problem:**" in text
        assert "**Out of Scope:**" in text


class TestSpecReviewerAudit:
    def test_phase_1_present(self):
        text = read_skill("spec-review")
        assert "## Phase 1" in text

    def test_phase_2_present(self):
        text = read_skill("spec-review")
        assert "## Phase 2" in text

    def test_phase_3_present(self):
        text = read_skill("spec-review")
        assert "## Phase 3" in text

    def test_output_format_present(self):
        text = read_skill("spec-review")
        assert "## Output Format" in text

    def test_approved_verdict_present(self):
        text = read_skill("spec-review")
        assert "APPROVED" in text

    def test_no_bad_good_examples(self):
        text = read_skill("spec-review")
        assert "BAD:" not in text
        assert "GOOD:" not in text


class TestPlanReviewerAudit:
    def test_phase_1_present(self):
        text = read_skill("plan-review")
        assert "## Phase 1" in text

    def test_phase_2_present(self):
        text = read_skill("plan-review")
        assert "## Phase 2" in text

    def test_phase_3_present(self):
        text = read_skill("plan-review")
        assert "## Phase 3" in text

    def test_output_format_present(self):
        text = read_skill("plan-review")
        assert "## Output Format" in text

    def test_tdd_structure_check_present(self):
        text = read_skill("plan-review")
        assert "TDD structure" in text

    def test_no_bad_good_examples(self):
        text = read_skill("plan-review")
        assert "BAD:" not in text
        assert "GOOD:" not in text


class TestImplReviewerAudit:
    def test_phase_1_present(self):
        text = read_skill("impl-review")
        assert "## Phase 1" in text

    def test_phase_2_present(self):
        text = read_skill("impl-review")
        assert "## Phase 2" in text

    def test_phase_3_present(self):
        text = read_skill("impl-review")
        assert "## Phase 3" in text

    def test_output_format_present(self):
        text = read_skill("impl-review")
        assert "## Output Format" in text

    def test_ac_coverage_check_present(self):
        text = read_skill("impl-review")
        assert "AC coverage" in text

    def test_no_bad_good_examples(self):
        text = read_skill("impl-review")
        assert "BAD:" not in text
        assert "GOOD:" not in text


class TestDebugPruning:
    def test_illustrative_pytest_path_absent(self):
        text = read_skill("debug")
        assert "tests/path/test_file.py::TestClass::test_method" not in text, (
            "Illustrative pytest path example must be removed"
        )

    def test_reproduce_step_preserved(self):
        text = read_skill("debug")
        assert "ทำซ้ำ bug" in text
        assert "Reproduce" in text

    def test_isolate_step_preserved(self):
        text = read_skill("debug")
        assert "แยกปัญหา" in text
        assert "Isolate" in text

    def test_fix_step_preserved(self):
        text = read_skill("debug")
        assert "แก้ bug" in text

    def test_verify_step_preserved(self):
        text = read_skill("debug")
        assert "ตรวจยืนยัน" in text
        assert "make test-unit" in text

    def test_rules_preserved(self):
        text = read_skill("debug")
        assert "Never comment out a failing test" in text
        assert "Stuck after 2 attempts" in text


class TestVerifyPruning:
    def test_preamble_sentence_absent(self):
        text = read_skill("verify")
        assert "Catch problems before they reach main." not in text, "Preamble sentence must be removed"

    def test_test_section_preserved(self):
        text = read_skill("verify")
        assert "make test-unit" in text
        assert "make test-int" in text

    def test_todo_grep_preserved(self):
        text = read_skill("verify")
        assert "TODO\\|FIXME\\|PLACEHOLDER" in text

    def test_summary_block_preserved(self):
        text = read_skill("verify")
        assert "Verification complete:" in text
        assert "Ready to ship" in text

    def test_documentation_section_preserved(self):
        text = read_skill("verify")
        assert "CLAUDE.md" in text
        assert "README.md" in text
