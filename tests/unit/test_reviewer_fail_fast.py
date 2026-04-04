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
        assert "Return ALL issues found" in skill_text("spec-reviewer"), \
            "spec-reviewer must instruct reviewer to return ALL issues"
        assert "do not stop at the first issue" in skill_text("spec-reviewer"), \
            "spec-reviewer must instruct reviewer not to stop at first issue"

    def test_plan_reviewer_all_issues_instruction(self):
        assert "Return ALL issues found" in skill_text("plan-reviewer"), \
            "plan-reviewer must instruct reviewer to return ALL issues"
        assert "do not stop at the first issue" in skill_text("plan-reviewer"), \
            "plan-reviewer must instruct reviewer not to stop at first issue"

    def test_impl_reviewer_all_issues_instruction(self):
        assert "Return ALL issues found" in skill_text("impl-reviewer"), \
            "impl-reviewer must instruct reviewer to return ALL issues"
        assert "do not stop at the first issue" in skill_text("impl-reviewer"), \
            "impl-reviewer must instruct reviewer not to stop at first issue"

    def test_spec_reviewer_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text("spec-reviewer"), \
            "spec-reviewer must not contain old 3-iteration cap"

    def test_plan_reviewer_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text("plan-reviewer"), \
            "plan-reviewer must not contain old 3-iteration cap"

    def test_impl_reviewer_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text("impl-reviewer"), \
            "impl-reviewer must not contain old 3-iteration cap"

    def test_spec_reviewer_new_max(self):
        assert "Max 2 total iterations" in skill_text("spec-reviewer"), \
            "spec-reviewer must declare Max 2 total iterations"

    def test_plan_reviewer_new_max(self):
        assert "Max 2 total iterations" in skill_text("plan-reviewer"), \
            "plan-reviewer must declare Max 2 total iterations"

    def test_impl_reviewer_new_max(self):
        assert "Max 2 total iterations" in skill_text("impl-reviewer"), \
            "impl-reviewer must declare Max 2 total iterations"


class TestCommandIterationLogic:
    def test_zie_plan_no_old_max(self):
        assert "Max 3 iterations" not in command_text("plan"), \
            "zie-plan must not contain old Max 3 iterations"

    def test_zie_plan_new_max(self):
        assert "Max 2 total iterations" in command_text("plan"), \
            "zie-plan must declare Max 2 total iterations"

    def test_zie_plan_confirm_pass(self):
        assert "confirm" in command_text("plan").lower(), \
            "zie-plan reviewer gate must mention a confirm pass"

    def test_zie_plan_zero_issues_fast_path(self):
        text = command_text("plan")
        assert "0 issues" in text or "APPROVED immediately" in text, \
            "zie-plan must describe 0-issues fast path"

    def test_zie_implement_no_old_max(self):
        assert "Max 3 total iterations" not in command_text("implement"), \
            "zie-implement must not contain old Max 3 total iterations"

    def test_zie_implement_new_max(self):
        assert "Max 2 total iterations" in command_text("implement"), \
            "zie-implement must declare Max 2 total iterations"

    def test_zie_implement_confirm_pass(self):
        assert "confirm" in command_text("implement").lower(), \
            "zie-implement impl-reviewer step must mention a confirm pass"

    def test_zie_implement_zero_issues_fast_path(self):
        text = command_text("implement")
        assert "0 issues" in text or "APPROVED immediately" in text, \
            "zie-implement must describe 0-issues fast path"


ADR_014 = Path(__file__).parents[2] / "zie-framework" / "decisions" / "ADR-014-async-impl-reviewer-deferred-check.md"


class TestADR014Amendment:
    def test_adr_014_has_amendment_section(self):
        text = ADR_014.read_text()
        assert "## Amendment" in text, \
            "ADR-014 must contain an ## Amendment section"

    def test_adr_014_amendment_mentions_new_cap(self):
        text = ADR_014.read_text()
        amendment_start = text.index("## Amendment")
        amendment_text = text[amendment_start:]
        assert "2" in amendment_text, \
            "ADR-014 amendment must reference the new iteration cap of 2"

    def test_adr_014_amendment_mentions_reviewer_fail_fast(self):
        text = ADR_014.read_text()
        amendment_start = text.index("## Amendment")
        amendment_text = text[amendment_start:]
        assert "reviewer-fail-fast" in amendment_text, \
            "ADR-014 amendment must reference the reviewer-fail-fast feature"
