---
approved: false
approved_at:
backlog: backlog/sprint-agent-audit.md
---

# Replace Phase 3 Agent with Inline Skill in /zie-sprint — Implementation Plan

**Goal:** Remove per-item `Agent(...)` wrapper from Phase 3 of `/zie-sprint` and replace with inline `Skill(zie-framework:zie-implement, slug)` calls.
**Architecture:** Phase 1 (parallel spec Agents) unchanged. Phase 3: per-item → read plan → inline Skill → handle result. No background overhead. Phases 2, 4, 5 unchanged.
**Tech Stack:** Markdown (commands/zie-sprint.md)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-sprint.md` | Replace Phase 3 per-item Agent loop with inline Skill call |

---

## Task 1: Replace Phase 3 Agent with inline Skill

**Acceptance Criteria:**
- Phase 3 contains zero `Agent(` (per-item) matches
- Uses `Skill(zie-framework:zie-implement, <slug>)`
- Reads only `zie-framework/plans/*-<slug>.md` per item
- Failure: `[impl N/total] <slug> ❌ <issue>` + halt
- Phase 1 Agents remain (parallel spec/plan still uses Agents)

**Files:**
- Modify: `commands/zie-sprint.md`

- [ ] **Step 1: Write failing tests (RED)**

Create `tests/unit/test_zie_sprint_phase3.py`:
```python
import re
from pathlib import Path

def test_phase3_no_agent():
    content = Path("commands/zie-sprint.md").read_text()
    phase3 = re.search(r"^## Phase 3.*?(?=^## Phase |\Z)", content, re.MULTILINE | re.DOTALL)
    assert phase3, "Phase 3 not found"
    assert "Agent(" not in phase3.group(0), "Phase 3 must not use Agent"

def test_phase3_has_skill():
    content = Path("commands/zie-sprint.md").read_text()
    phase3 = re.search(r"^## Phase 3.*?(?=^## Phase |\Z)", content, re.MULTILINE | re.DOTALL)
    assert "Skill(" in phase3.group(0) and "zie-implement" in phase3.group(0)

def test_phase1_keeps_agent():
    content = Path("commands/zie-sprint.md").read_text()
    phase1 = re.search(r"^## Phase 1.*?(?=^## Phase |\Z)", content, re.MULTILINE | re.DOTALL)
    assert "Agent(" in phase1.group(0), "Phase 1 must keep Agents"
```

Run: `make test-unit` — FAILS

- [ ] **Step 2: Implement (GREEN)**

Edit `commands/zie-sprint.md` Phase 3 section. Replace per-item Agent loop with:

```markdown
3. **Implement each item** (WIP=1 — strictly sequential):

   For each item in priority order:
   - Read `zie-framework/plans/*-<slug>.md` (only this file per item)
   - Invoke: `Skill(zie-framework:zie-implement, <slug>)`
   - Success: `[impl N/total] <slug> ✓ <commit>`
   - Failure: `[impl N/total] <slug> ❌ <issue>` → halt sprint
```

Remove: `Agent(...)`, `run_in_background`, pre-load optimization mentions.
Keep: Phase 1 Agents, priority order, WIP=1 constraint, phases 2/4/5.

Run: `make test-unit` — PASSES

- [ ] **Step 3: Refactor**

Polish prose. Verify Phase 1 Agents still present. Trim redundancy.

Run: `make test-unit` — PASS
