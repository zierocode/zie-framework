from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestImplementProgress:
    def test_task_counter_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "[T" in text and "/N]" in text or "[T{N}" in text or "[T{n}" in text.lower(), \
            "zie-implement.md must contain task counter notation [TN/total]"

    def test_red_phase_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "→ TDD loop" in text or "Skill(zie-framework:tdd-loop)" in text, \
            "zie-implement.md must contain → TDD loop marker or Skill(zie-framework:tdd-loop) invocation"

    def test_green_phase_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "Skill(zie-framework:tdd-loop)" in text, \
            "zie-implement.md must invoke Skill(zie-framework:tdd-loop) (covers GREEN phase)"

    def test_refactor_phase_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "REFACTOR" in text, "zie-implement.md must mention REFACTOR phase"

    def test_task_done_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "done —" in text, "zie-implement.md must contain 'done —' completion marker"

    def test_checkpoint_marker_present(self):
        text = (COMMANDS_DIR / "implement.md").read_text()
        assert "heckpoint" in text, "zie-implement.md must contain checkpoint summary marker"


class TestAuditProgress:
    """zie-audit skill is canonical implementation since lean-dual-audit-pipeline."""

    def _skill(self):
        return (Path(__file__).parents[2] / "skills" / "zie-audit" / "SKILL.md").read_text()

    def test_phase_structure_present(self):
        text = self._skill()
        assert "## Phase 1" in text and "## Phase 2" in text, \
            "zie-audit skill must contain Phase 1 and Phase 2 sections"

    def test_three_dimension_agents_present(self):
        text = self._skill()
        assert "Agent A" in text and "Agent B" in text and "Agent C" in text, \
            "zie-audit skill must describe dimension agents (A, B, C...)"

    def test_research_parallel_dispatch_present(self):
        text = self._skill()
        assert "parallel" in text.lower() or "simultaneously" in text.lower(), \
            "zie-audit skill must describe parallel agent dispatch"

    def test_synthesis_phase_present(self):
        text = self._skill()
        assert "## Phase 4" in text and ("Synthesis" in text or "synthesis" in text), \
            "zie-audit skill must contain a Synthesis phase"


class TestReleaseProgress:
    def test_gate_1_counter_present(self):
        text = (COMMANDS_DIR / "release.md").read_text()
        assert "[Gate 1/5]" in text, \
            "zie-release.md must contain [Gate 1/5] counter"

    def test_gate_2_counter_present(self):
        text = (COMMANDS_DIR / "release.md").read_text()
        assert "[Gate 2/5]" in text, \
            "zie-release.md must contain [Gate 2/5] counter"

    def test_step_counter_present(self):
        text = (COMMANDS_DIR / "release.md").read_text()
        assert "[Step " in text, \
            "zie-release.md must contain [Step N/M] post-gate step counter"


class TestPlanProgress:
    def test_plan_counter_present(self):
        text = (COMMANDS_DIR / "plan.md").read_text()
        assert "[Plan " in text, \
            "zie-plan.md must contain [Plan N/M] counter notation"

    def test_reviewer_pass_marker_present(self):
        text = (COMMANDS_DIR / "plan.md").read_text()
        assert "plan-reviewer pass" in text, \
            "zie-plan.md must contain 'plan-reviewer pass' marker"


class TestResyncProgress:
    def test_exploring_marker_present(self):
        text = (COMMANDS_DIR / "resync.md").read_text()
        assert "Exploring codebase" in text, \
            "zie-resync.md must contain 'Exploring codebase...' start marker"

    def test_explored_completion_marker_present(self):
        text = (COMMANDS_DIR / "resync.md").read_text()
        assert "Explored" in text, \
            "zie-resync.md must contain 'Explored' completion marker"


class TestRetroProgress:
    def test_adr_counter_present(self):
        text = (COMMANDS_DIR / "retro.md").read_text()
        assert "[ADR " in text, \
            "zie-retro.md must contain [ADR N/M] counter notation"

    def test_analyzing_git_log_marker_present(self):
        text = (COMMANDS_DIR / "retro.md").read_text()
        assert "Analyzing git log" in text, \
            "zie-retro.md must contain 'Analyzing git log' phase marker"

    def test_updating_knowledge_docs_marker_present(self):
        text = (COMMANDS_DIR / "retro.md").read_text()
        assert "Updating knowledge docs" in text, \
            "zie-retro.md must contain 'Updating knowledge docs' phase marker"
