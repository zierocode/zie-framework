import re
from pathlib import Path

SPRINT_CMD = Path("commands/sprint.md")


def test_phase2_no_agent():
    content = SPRINT_CMD.read_text()
    phase2 = re.search(r"^## PHASE 2.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase2, "Phase 2 not found"
    assert "Agent(" not in phase2.group(0), "Phase 2 (implement) must not use Agent"


def test_phase2_has_skill():
    content = SPRINT_CMD.read_text()
    phase2 = re.search(r"^## PHASE 2.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase2, "Phase 2 not found"
    assert "Skill(" in phase2.group(0) and "zie-implement" in phase2.group(0)


def test_phase1_keeps_agent():
    content = SPRINT_CMD.read_text()
    phase1 = re.search(r"^## PHASE 1.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase1, "Phase 1 not found"
    assert "Agent(" in phase1.group(0), "Phase 1 must keep Agents"
