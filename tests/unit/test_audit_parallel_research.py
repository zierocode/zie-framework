from pathlib import Path

COMMANDS_DIR = Path(__file__).parents[2] / "commands"


def _phase2_text() -> str:
    """Extract the Phase 2 section from zie-audit.md."""
    text = (COMMANDS_DIR / "zie-audit.md").read_text()
    start = text.index("## Phase 2")
    end = text.index("## Phase 3", start)
    return text[start:end]


def _phase3_text() -> str:
    """Extract the Phase 3 section from zie-audit.md."""
    text = (COMMANDS_DIR / "zie-audit.md").read_text()
    start = text.index("## Phase 3")
    end = text.index("## Phase 4", start)
    return text[start:end]


class TestAuditParallelResearch:
    def test_parallel_dispatch_instruction_present(self):
        phase2 = _phase2_text()
        assert "parallel" in phase2.lower() or "simultaneously" in phase2.lower(), (
            "Phase 2 must instruct dispatching agents in parallel/simultaneously"
        )

    def test_sequential_loop_instruction_absent(self):
        phase2 = _phase2_text()
        assert "for query in queries" not in phase2, (
            "Phase 2 must not contain a sequential 'for query in queries' loop instruction"
        )

    def test_synthesis_agent_has_no_websearch(self):
        phase3 = _phase3_text()
        assert "no WebSearch" in phase3 or "0 WebSearch" in phase3, (
            "Phase 3 synthesis agent must explicitly have no WebSearch"
        )
