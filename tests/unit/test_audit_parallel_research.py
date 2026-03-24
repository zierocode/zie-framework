from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def _phase3_text() -> str:
    """Extract the Phase 3 section from zie-audit.md."""
    text = (COMMANDS_DIR / "zie-audit.md").read_text()
    # Slice from Phase 3 header to Historical Diff header (inserted by T15 between Phase 4 and Phase 5)
    start = text.index("## Phase 3")
    end = text.index("## Phase 4", start)
    return text[start:end]


class TestAuditParallelResearch:
    def test_parallel_dispatch_instruction_present(self):
        phase3 = _phase3_text()
        assert "parallel" in phase3.lower(), (
            "Phase 3 must instruct dispatching WebSearch calls in parallel"
        )

    def test_sequential_loop_instruction_absent(self):
        phase3 = _phase3_text()
        assert "for query in queries" not in phase3, (
            "Phase 3 must not contain a sequential 'for query in queries' loop instruction"
        )

    def test_research_unavailable_fallback_present(self):
        phase3 = _phase3_text()
        assert "Research unavailable" in phase3, (
            "Phase 3 must contain 'Research unavailable' fallback for failed queries"
        )
