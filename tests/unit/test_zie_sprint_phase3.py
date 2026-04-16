import re
from pathlib import Path

SPRINT_CMD = Path("commands/sprint.md")


def test_phase2_no_agent():
    content = SPRINT_CMD.read_text()
    phase2 = re.search(r"^## PHASE 2.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase2, "Phase 2 not found"
    assert "Agent(" not in phase2.group(0), "Phase 2 (implement) must not use Agent"


def test_phase2_uses_make_zie_implement():
    """Phase 2 must invoke make zie-implement (agent mode) — Skill(zie-implement) does not exist."""
    content = SPRINT_CMD.read_text()
    phase2 = re.search(r"^## PHASE 2.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase2, "Phase 2 not found"
    phase2_text = phase2.group(0)
    assert "zie-implement" in phase2_text, "Phase 2 must reference zie-implement (make zie-implement agent invocation)"
    assert "Skill(zie-framework:zie-implement" not in phase2_text, (
        "Phase 2 must not call non-existent Skill zie-implement — use make zie-implement"
    )


def test_phase1_uses_skill_calls():
    content = SPRINT_CMD.read_text()
    phase1 = re.search(r"^## PHASE 1.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase1, "Phase 1 not found"
    assert "Skill(" in phase1.group(0), "Phase 1 must use direct Skill calls (no intermediate Agent spawn)"
