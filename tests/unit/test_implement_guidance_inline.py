from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "zie-implement.md"


def read_cmd() -> str:
    return CMD.read_text()


class TestInlineGuidanceBlock:
    def test_inline_tdd_guidance_present(self):
        text = read_cmd()
        assert "RED" in text and "GREEN" in text and "REFACTOR" in text, \
            "Inline TDD guidance block must contain RED, GREEN, REFACTOR"

    def test_inline_test_pyramid_rule_present(self):
        text = read_cmd()
        assert "unit" in text and "integration" in text and "e2e" in text, \
            "Inline test-pyramid rule must name unit, integration, and e2e"

    def test_per_task_tdd_loop_skill_absent(self):
        text = read_cmd()
        assert 'Invoke `Skill(zie-framework:tdd-loop)` for RED/GREEN/REFACTOR guidance' not in text, \
            "Old per-task tdd-loop invocation line must not appear in zie-implement.md"

    def test_test_pyramid_skill_absent(self):
        text = read_cmd()
        assert "Skill(zie-framework:test-pyramid)" not in text, \
            "Skill(zie-framework:test-pyramid) must not appear anywhere in zie-implement.md"

    def test_tdd_deep_conditional_present(self):
        text = read_cmd()
        assert "tdd: deep" in text, \
            "Conditional Skill(tdd-loop) for tdd: deep hint must be present"
        assert "Skill(zie-framework:tdd-loop)" in text, \
            "Skill(zie-framework:tdd-loop) must still appear for tdd: deep path"


class TestParallelByDefault:
    def test_parallel_by_default_logic_present(self):
        text = read_cmd()
        assert "no depends_on" in text or "without depends_on" in text or \
               "no `depends_on`" in text, \
            "Parallel-by-default logic must state tasks without depends_on run in parallel"

    def test_depends_on_sequential_logic_present(self):
        text = read_cmd()
        assert "depends_on" in text, \
            "Sequential depends_on annotation logic must still be present"
