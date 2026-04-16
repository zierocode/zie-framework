"""Tests for the unified review skill's fail-fast and iteration behavior."""

from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILLS_DIR = ROOT / "skills"
REVIEW_SKILL = SKILLS_DIR / "review" / "SKILL.md"


def skill_text() -> str:
    return REVIEW_SKILL.read_text()


class TestReviewerOutputInstructions:
    def test_review_returns_all_issues(self):
        assert "Return ALL issues found" in skill_text(), "review must instruct to return ALL issues"

    def test_review_no_old_max(self):
        assert "Max 3 review iterations" not in skill_text(), "review must not contain old 3-iteration cap"

    def test_review_new_max(self):
        assert "Max 2 iterations" in skill_text(), "review must declare Max 2 iterations"


class TestCommandIterationLogic:
    def test_zie_plan_no_old_max(self):
        text = (ROOT / "commands" / "plan.md").read_text()
        assert "Max 3 iterations" not in text, "zie-plan must not contain old Max 3 iterations"

    def test_zie_plan_single_reviewer_pass(self):
        text = (ROOT / "commands" / "plan.md").read_text()
        assert "fix ALL issues inline" in text or "inline verification" in text, (
            "zie-plan must describe single reviewer pass with inline fixes"
        )

    def test_zie_plan_confirm_pass(self):
        text = (ROOT / "commands" / "plan.md").read_text()
        assert "confirm" in text.lower(), "zie-plan reviewer gate must mention a confirm pass"

    def test_zie_plan_zero_issues_fast_path(self):
        text = (ROOT / "commands" / "plan.md").read_text()
        assert "Auto-approve" in text or "initial scan" in text, (
            "zie-plan must describe 0-issues fast path (auto-approve on initial scan)"
        )

    def test_zie_implement_no_old_max(self):
        text = (ROOT / "commands" / "implement.md").read_text()
        assert "Max 3 total iterations" not in text, (
            "zie-implement must not contain old Max 3 total iterations"
        )

    def test_zie_implement_new_max(self):
        text = (ROOT / "commands" / "implement.md").read_text().lower()
        assert "1 retry" in text or "retry" in text, "zie-implement must describe 1-retry auto-fix protocol"

    def test_zie_implement_confirm_pass(self):
        text = (ROOT / "commands" / "implement.md").read_text().lower()
        assert "pass" in text and ("fix" in text or "inline" in text), (
            "zie-implement inline reviewer step must describe pass/fix outcome"
        )

    def test_zie_implement_zero_issues_fast_path(self):
        text = (ROOT / "commands" / "implement.md").read_text().lower()
        assert "no issues" in text or "✅" in text or "approved" in text, (
            "zie-implement must describe zero-issues fast path"
        )


ADR_014 = ROOT / "zie-framework" / "decisions" / "ADR-014-async-impl-review-deferred-check.md"


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