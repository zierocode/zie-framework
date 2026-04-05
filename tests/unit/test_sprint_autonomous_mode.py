from pathlib import Path

CMD = Path(__file__).parents[2] / "commands" / "sprint.md"


def text():
    return CMD.read_text()


class TestSprintAutonomousMode:
    def test_autonomous_mode_context_variable(self):
        assert "autonomous_mode" in text(), \
            "sprint.md must set autonomous_mode context variable"

    def test_clarity_detection_present(self):
        t = text().lower()
        assert "clarity" in t or ("score" in t and "problem" in t), \
            "sprint.md must include backlog clarity detection logic"

    def test_phase1_calls_autonomous_spec_design(self):
        t = text()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert "autonomous" in phase1.lower(), \
            "Phase 1 must call spec-design with autonomous mode"

    def test_phase1_no_intermediate_agent_spawn(self):
        t = text()
        phase1_idx = t.index("PHASE 1")
        phase2_idx = t.index("PHASE 2")
        phase1 = t[phase1_idx:phase2_idx]
        assert 'subagent_type="general-purpose"' not in phase1 and \
               "subagent_type='general-purpose'" not in phase1, \
            "Phase 1 must not spawn general-purpose agent intermediary"

    def test_phase4_auto_retro(self):
        t = text()
        phase4_idx = t.index("PHASE 4")
        phase4 = t[phase4_idx:]
        assert "auto" in phase4.lower() or "automatically" in phase4.lower(), \
            "Phase 4 must auto-run retro without user prompt"

    def test_interruption_protocol_documented(self):
        t = text().lower()
        assert "interrupt" in t or "interruption" in t, \
            "sprint.md must document when to interrupt user"
