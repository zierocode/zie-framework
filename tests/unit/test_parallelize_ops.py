"""Tests for Sprint D: parallelize-framework-ops — parallel ADR writes and ROADMAP update."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


class TestRetroParallelADRAndRoadmap:
    def test_retro_launches_adr_and_roadmap_in_parallel(self):
        """retro.md must instruct parallel ADR writes + ROADMAP update."""
        content = (REPO_ROOT / "commands" / "retro.md").read_text()
        assert "parallel" in content.lower(), (
            "retro.md must instruct parallel ADR writes and ROADMAP update"
        )

    def test_retro_parallel_note_explains_no_race(self):
        """retro.md parallel note must confirm different target files (no race condition)."""
        content = (REPO_ROOT / "commands" / "retro.md").read_text()
        assert "different target files" in content or "no race" in content.lower(), (
            "retro.md must note that parallel ADR+ROADMAP writes have no race condition"
        )

    def test_retro_adr_summary_after_parallel(self):
        """ADR-000-summary update section must come AFTER the parallel ADR+ROADMAP step."""
        content = (REPO_ROOT / "commands" / "retro.md").read_text()
        parallel_pos = content.lower().find("parallel")
        assert parallel_pos != -1, "parallel instruction missing"
        # Find the "Update ADR-000-summary" instruction that follows the parallel block
        after_parallel = content[parallel_pos:]
        assert "ADR-000-summary.md" in after_parallel, (
            "ADR-000-summary.md update section must appear after the parallel launch instruction"
        )


class TestAuditAlreadyParallel:
    def test_zie_audit_skill_uses_parallel_agents(self):
        """audit skill must already spawn parallel agents for dimensions."""
        content = (REPO_ROOT / "skills" / "audit" / "SKILL.md").read_text()
        assert "parallel" in content.lower(), (
            "audit skill must use parallel agents for audit dimensions"
        )
