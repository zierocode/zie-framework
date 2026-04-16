from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestVerifyScopedMode:
    def test_scope_parameter_declared(self):
        text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
        assert "scope" in text, "verify SKILL.md must declare a scope parameter"

    def test_tests_only_branch_present(self):
        text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
        assert "tests-only" in text, "verify SKILL.md must contain a tests-only branch"

    def test_full_scope_default_declared(self):
        text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
        assert "full" in text, "verify SKILL.md must declare full as a scope value"


class TestZieFixScopeParam:
    def test_zie_fix_passes_scope_tests_only(self):
        text = (COMMANDS_DIR / "fix.md").read_text()
        assert "scope=tests-only" in text, "zie-fix.md must pass scope=tests-only to Skill(zie-framework:verify)"


class TestVerifyCheck2TestOutputGuard:
    def _text(self):
        return (SKILLS_DIR / "verify" / "SKILL.md").read_text()

    def test_check1_has_test_output_guard(self):
        """Check 1 must document the test_output guard before running make test-unit."""
        text = self._text()
        check1_idx = text.find("### 1.")
        check2_idx = text.find("### 2.")
        check1_section = text[check1_idx:check2_idx]
        assert "test_output" in check1_section, "verify SKILL.md check 1 must mention test_output guard"

    def test_check2_has_test_output_guard(self):
        """Check 2 must reuse test_output — not re-run make test-unit."""
        text = self._text()
        check2_idx = text.find("### 2.")
        check3_idx = text.find("### 3.")
        check2_section = text[check2_idx:check3_idx]
        assert "test_output" in check2_section, (
            "verify SKILL.md check 2 must guard against re-running make test-unit when test_output is already provided"
        )

    def test_check2_no_re_run_instruction(self):
        """Check 2 must not instruct Claude to run the full suite when test_output is provided."""
        text = self._text()
        check2_idx = text.find("### 2.")
        check3_idx = text.find("### 3.")
        check2_section = text[check2_idx:check3_idx]
        assert "do NOT re-run" in check2_section or "not re-run" in check2_section.lower(), (
            "verify check 2 must explicitly say NOT to re-run make test-unit"
        )
