from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"
COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestVerifyScopedMode:
    def test_scope_parameter_declared(self):
        text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
        assert "scope" in text, \
            "verify SKILL.md must declare a scope parameter"

    def test_tests_only_branch_present(self):
        text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
        assert "tests-only" in text, \
            "verify SKILL.md must contain a tests-only branch"

    def test_full_scope_default_declared(self):
        text = (SKILLS_DIR / "verify" / "SKILL.md").read_text()
        assert "full" in text, \
            "verify SKILL.md must declare full as a scope value"


class TestZieFixScopeParam:
    def test_zie_fix_passes_scope_tests_only(self):
        text = (COMMANDS_DIR / "fix.md").read_text()
        assert "scope=tests-only" in text, \
            "zie-fix.md must pass scope=tests-only to Skill(zie-framework:verify)"
