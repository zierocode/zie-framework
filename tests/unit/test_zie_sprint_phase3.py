import re
from pathlib import Path

SPRINT_CMD = Path("commands/zie-sprint.md")


def test_phase3_no_agent():
    content = SPRINT_CMD.read_text()
    phase3 = re.search(r"^## PHASE 3.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase3, "Phase 3 not found"
    assert "Agent(" not in phase3.group(0), "Phase 3 must not use Agent"


def test_phase3_has_skill():
    content = SPRINT_CMD.read_text()
    phase3 = re.search(r"^## PHASE 3.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase3, "Phase 3 not found"
    assert "Skill(" in phase3.group(0) and "zie-implement" in phase3.group(0)


def test_phase1_keeps_agent():
    content = SPRINT_CMD.read_text()
    phase1 = re.search(r"^## PHASE 1.*?(?=^## PHASE |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase1, "Phase 1 not found"
    assert "Agent(" in phase1.group(0), "Phase 1 must keep Agents"
