from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILLS_DIR = ROOT / "skills"
COMMANDS_DIR = ROOT / "commands"


def skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def command_text(name: str) -> str:
    return (COMMANDS_DIR / f"{name}.md").read_text()


class TestReviewerOutputInstructions:
    def test_spec_reviewer_all_issues_instruction(self):
        assert "Return ALL issues found" in skill_text("spec-review"), (
            "spec-review must instruct reviewer to return ALL issues"
        )
        assert "don't stop at the first issue" in skill_text("spec-review"), (
            "spec-review must instruct reviewer not to stop at first issue"
        )

    def test_plan_reviewer_all_issues_instruction(self):
        assert "Return ALL issues found" in skill_text("plan-review"), (
            "plan-review must instruct reviewer to return ALL issues"
        )
        assert "don't stop at the first issue" in skill_text("plan-review"), (
            "plan-review must instruct reviewer not to stop at first issue"
        )

    def test_impl_reviewer_all_issues_instruction(self):
        assert "Return ALL issues found" in skill_text("impl-review"), (
            "impl-review must instruct reviewer to return ALL issues"
        )
        assert "don't stop at the first issue" in skill_text("impl-review"), (
            "impl-review must instruct reviewer not to stop at first issue"
        )

    def test_spec_reviewer_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text("spec-review"), (
            "spec-review must not contain old 3-iteration cap"
        )

    def test_plan_reviewer_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text("plan-review"), (
            "plan-review must not contain old 3-iteration cap"
        )

    def test_impl_reviewer_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text("impl-review"), (
            "impl-review must not contain old 3-iteration cap"
        )

    def test_spec_reviewer_new_max(self):
        assert "Max 2 iterations" in skill_text("spec-review"), "spec-review must declare Max 2 iterations"

    def test_plan_reviewer_new_max(self):
        assert "Max 2 iterations" in skill_text("plan-review"), "plan-review must declare Max 2 iterations"

    def test_impl_reviewer_new_max(self):
        assert "Max 2 iterations" in skill_text("impl-review"), "impl-review must declare Max 2 iterations"


class TestCommandIterationLogic:
    def test_zie_plan_no_old_max(self):
        assert "Max 3 iterations" not in command_text("plan"), "zie-plan must not contain old Max 3 iterations"

    def test_zie_plan_single_reviewer_pass(self):
        text = command_text("plan")
        assert "no re-invocation" in text.lower() or "inline verification" in text.lower(), (
            "zie-plan must describe single reviewer pass with inline fixes"
        )

    def test_zie_plan_confirm_pass(self):
        assert "confirm" in command_text("plan").lower(), "zie-plan reviewer gate must mention a confirm pass"

    def test_zie_plan_zero_issues_fast_path(self):
        text = command_text("plan")
        assert "Auto-approve" in text or "initial scan" in text, (
            "zie-plan must describe 0-issues fast path (auto-approve on initial scan)"
        )

    def test_zie_implement_no_old_max(self):
        assert "Max 3 total iterations" not in command_text("implement"), (
            "zie-implement must not contain old Max 3 total iterations"
        )

    def test_zie_implement_new_max(self):
        text = command_text("implement").lower()
        assert "1 retry" in text or "retry" in text, "zie-implement must describe 1-retry auto-fix protocol"

    def test_zie_implement_confirm_pass(self):
        text = command_text("implement").lower()
        assert "pass" in text and ("fix" in text or "inline" in text), (
            "zie-implement inline reviewer step must describe pass/fix outcome"
        )

    def test_zie_implement_zero_issues_fast_path(self):
        text = command_text("implement").lower()
        assert "no issues" in text or "✅" in text or "approved" in text, (
            "zie-implement must describe zero-issues fast path"
        )


ADR_014 = Path(__file__).parents[2] / "zie-framework" / "decisions" / "ADR-014-async-impl-review-deferred-check.md"


class TestADR014Amendment:
    def test_adr_014_has_amendment_section(self):
        text = ADR_014.read_text()
        assert "## Amendment" in text, "ADR-014 must contain an ## Amendment section"

    def test_adr_014_amendment_mentions_new_cap(self):
        text = ADR_014.read_text()
        amendment_start = text.index("## Amendment")
        amendment_text = text[amendment_start:]
        assert "2" in amendment_text, "ADR-014 amendment must reference the new iteration cap of 2"

    def test_adr_014_amendment_mentions_reviewer_fail_fast(self):
        text = ADR_014.read_text()
        amendment_start = text.index("## Amendment")
        amendment_text = text[amendment_start:]
        assert "reviewer-fail-fast" in amendment_text, "ADR-014 amendment must reference the reviewer-fail-fast feature"
