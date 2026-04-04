from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "implement.md"


def read_cmd() -> str:
    return CMD.read_text()


class TestInlineGuidanceBlock:
    def test_inline_tdd_guidance_present(self):
        text = read_cmd()
        assert "Skill(zie-framework:tdd-loop)" in text, \
            "zie-implement.md must invoke Skill(zie-framework:tdd-loop) in the Task Loop"

    def test_inline_test_pyramid_rule_present(self):
        text = read_cmd()
        assert "unit" in text and "integration" in text and "e2e" in text, \
            "Inline test-pyramid rule must name unit, integration, and e2e"

    def test_per_task_tdd_loop_skill_present(self):
        text = read_cmd()
        assert "Skill(zie-framework:tdd-loop)" in text, \
            "Skill(zie-framework:tdd-loop) must appear in zie-implement.md"

    def test_test_pyramid_skill_absent(self):
        text = read_cmd()
        assert "Skill(zie-framework:test-pyramid)" not in text, \
            "Skill(zie-framework:test-pyramid) must not appear anywhere in zie-implement.md"

    def test_tdd_deep_conditional_absent(self):
        """tdd: deep gate is removed; tdd-loop is unconditional."""
        text = read_cmd()
        assert "tdd: deep" not in text, \
            "tdd: deep conditional must be removed from zie-implement.md"


class TestParallelByDefault:
    def test_parallel_execution_documented(self):
        text = read_cmd()
        assert "background" in text.lower() or "parallel" in text.lower() or \
               "concurrent" in text.lower(), \
            "zie-implement.md must document parallel/background execution"

    def test_sequential_task_loop_present(self):
        text = read_cmd()
        assert "Task Loop" in text or "task loop" in text.lower(), \
            "Sequential task loop structure must be documented"
