from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


class TestPlanLazyLoading:
    def test_header_only_read_instruction_present(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert (
            "Read plan header only: everything up to (not including) the first `### Task` heading"
            in text
        ), "zie-implement.md must contain the header-only read instruction"

    def test_per_task_section_read_instruction_present(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert (
            "Read this task's full section from the plan file (from its `### Task N` heading to the next `### Task` heading or EOF)"
            in text
        ), "zie-implement.md must contain the per-task section read instruction"

    def test_full_plan_read_at_startup_absent(self):
        text = (COMMANDS_DIR / "zie-implement.md").read_text()
        assert (
            "Read plan file → check frontmatter for `approved: true`" not in text
        ), "zie-implement.md must NOT contain the full-plan read at startup instruction"
