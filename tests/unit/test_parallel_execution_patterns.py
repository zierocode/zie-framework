"""Test parallel execution patterns."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
CMD_DIR = REPO_ROOT / "commands"
SKILLS_DIR = REPO_ROOT / "skills"
DOCS_DIR = REPO_ROOT / "zie-framework" / "docs"


class TestParallelExecutionPatterns:
    """Test that parallel execution patterns are correctly implemented."""

    def test_zie_implement_max_parallel_tasks(self):
        """zie-implement.md must specify max parallel tasks limit."""
        text = (CMD_DIR / "zie-implement.md").read_text()
        assert "Max parallel tasks" in text, \
            "zie-implement.md must specify max parallel tasks"
        assert "4" in text, \
            "zie-implement.md must specify limit of 4"

    def test_zie_implement_file_conflict_check(self):
        """zie-implement.md must include file conflict detection."""
        text = (CMD_DIR / "zie-implement.md").read_text()
        assert "conflict" in text.lower(), \
            "zie-implement.md must mention file conflict detection"

    def test_zie_plan_max_parallel_agents(self):
        """zie-plan.md must specify max parallel Agents limit."""
        text = (CMD_DIR / "zie-plan.md").read_text()
        assert "Max parallel Agents" in text or "max 4" in text.lower(), \
            "zie-plan.md must specify max parallel Agents"

    def test_zie_release_fork_terminology_fixed(self):
        """zie-release.md must not use misleading 'Fork Skill' terminology."""
        text = (CMD_DIR / "zie-release.md").read_text()
        # Either removed or converted to true async
        assert "Fork `Skill" not in text, \
            "zie-release.md must not use 'Fork `Skill' terminology"

    def test_depends_on_syntax_documented(self):
        """write-plan/SKILL.md must document depends_on syntax."""
        text = (SKILLS_DIR / "write-plan" / "SKILL.md").read_text()
        assert "depends_on" in text, \
            "write-plan/SKILL.md must document depends_on syntax"

    def test_plan_reviewer_suggests_depends_on(self):
        """plan-reviewer/SKILL.md must suggest depends_on for shared files."""
        text = (SKILLS_DIR / "plan-reviewer" / "SKILL.md").read_text()
        assert "depends_on" in text, \
            "plan-reviewer/SKILL.md must mention depends_on"
        assert "file conflict" in text.lower(), \
            "plan-reviewer/SKILL.md must mention file conflict detection"

    def test_parallel_docs_created(self):
        """zie-framework/docs/parallel-execution-patterns.md must exist."""
        assert (DOCS_DIR / "parallel-execution-patterns.md").exists(), \
            "parallel-execution-patterns.md must be created"


class TestFileConflictDetection:
    """Test file conflict detection logic (unit tests)."""

    def test_detect_conflicts_same_file(self):
        """File conflict detection must identify tasks writing to same file."""
        # Simple algorithm test - no import needed
        tasks = [
            {"id": "T1", "output_files": ["utils.py"]},
            {"id": "T2", "output_files": ["utils.py"]},
        ]

        file_writers = {}
        for task in tasks:
            for filepath in task["output_files"]:
                if filepath not in file_writers:
                    file_writers[filepath] = []
                file_writers[filepath].append(task["id"])

        conflicts = {fp: writers for fp, writers in file_writers.items() if len(writers) > 1}

        assert "utils.py" in conflicts
        assert "T1" in conflicts["utils.py"]
        assert "T2" in conflicts["utils.py"]

    def test_no_conflicts_different_files(self):
        """No conflicts when tasks write to different files."""
        tasks = [
            {"id": "T1", "output_files": ["utils.py"]},
            {"id": "T2", "output_files": ["config.py"]},
        ]

        file_writers = {}
        for task in tasks:
            for filepath in task["output_files"]:
                if filepath not in file_writers:
                    file_writers[filepath] = []
                file_writers[filepath].append(task["id"])

        conflicts = {fp: writers for fp, writers in file_writers.items() if len(writers) > 1}

        assert conflicts == {}
