"""Tests for parallel-release-gates Task 1: zie-release parallel gate execution."""
from pathlib import Path

CMD_PATH = Path(__file__).parents[2] / "commands" / "zie-release.md"


def cmd_text() -> str:
    return CMD_PATH.read_text()


class TestParallelReleaseGates:
    def test_docs_sync_spawns_before_gate1(self):
        """docs-sync-check Agent spawns before unit tests (Pre-Gate-1 section)."""
        text = cmd_text()
        pre_gate1_idx = text.find("Pre-Gate-1")
        gate1_idx = text.find("Gate 1/5")
        assert pre_gate1_idx > 0 and gate1_idx > pre_gate1_idx, \
            "Pre-Gate-1 docs-sync section must appear before Gate 1"

    def test_gates_2_3_4_spawn_simultaneously(self):
        """Gates 2, 3, 4 spawn simultaneously after Gate 1 passes."""
        text = cmd_text()
        assert "Spawn Parallel Gates 2" in text or "parallel" in text.lower(), \
            "Gates 2-4 must spawn in parallel after Gate 1 passes"

    def test_all_gate_failures_collected_before_stopping(self):
        """All gate results collected before version bump — no stop-at-first."""
        text = cmd_text()
        assert "Collect Parallel Gate Results" in text or "collect" in text.lower(), \
            "All gate results must be collected before stopping"
        assert "do NOT stop at first" in text or "all failures" in text.lower() or \
               "STOP before version bump" in text, \
            "Must collect all failures before stopping"

    def test_gate_agents_use_general_purpose(self):
        """Gate agents use subagent_type='general-purpose'."""
        text = cmd_text()
        # Count general-purpose in gate section
        assert text.count("general-purpose") >= 3, \
            "At least 3 general-purpose agent invocations for gates 2, 3, 4"

    def test_gate_agents_run_in_background(self):
        """Gate agents use run_in_background=True."""
        text = cmd_text()
        assert "run_in_background=True" in text or "run_in_background: true" in text.lower(), \
            "Gate agents must use run_in_background=True"

    def test_fallback_to_sequential_documented(self):
        """Fallback to sequential execution if Agent unavailable."""
        text = cmd_text()
        assert "fallback" in text.lower() and ("sequential" in text.lower() or "make test-int" in text), \
            "Must document fallback to sequential execution"
