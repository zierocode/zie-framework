from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "zie-audit" / "SKILL.md"


def _phase_text(n: int) -> str:
    """Extract Phase N section from zie-audit skill."""
    text = SKILL_PATH.read_text()
    header = f"## Phase {n}"
    next_header = f"## Phase {n + 1}"
    start = text.index(header)
    try:
        end = text.index(next_header, start)
    except ValueError:
        end = len(text)
    return text[start:end]


class TestAuditParallelResearch:
    def test_parallel_dispatch_instruction_present(self):
        phase2 = _phase_text(2)
        assert "parallel" in phase2.lower() or "simultaneously" in phase2.lower(), (
            "Phase 2 must instruct dispatching agents in parallel/simultaneously"
        )

    def test_sequential_loop_instruction_absent(self):
        phase2 = _phase_text(2)
        assert "for query in queries" not in phase2, (
            "Phase 2 must not contain a sequential 'for query in queries' loop instruction"
        )

    def test_synthesis_agent_has_no_websearch(self):
        phase4 = _phase_text(4)
        assert "no WebSearch" in phase4 or "0 WebSearch" in phase4, (
            "Phase 4 synthesis must explicitly have no WebSearch"
        )
