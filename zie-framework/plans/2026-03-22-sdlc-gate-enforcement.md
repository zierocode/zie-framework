---
approved: true
approved_at: 2026-03-22
backlog: backlog/sdlc-gate-enforcement.md
---

# SDLC Gate Enforcement + Parallel Agents — Implementation Plan

> **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.

**Goal:** Enforce idea → backlog → approved plan → build flow with auto-fallback, parallel agents (max 4), and compounding zie-memory across all commands.

**Architecture:** New `/zie-plan` command sits between `/zie-idea` and `/zie-build`. ROADMAP gains a Ready lane. `/zie-build` gains pre-flight gates and auto-spawns parallel agents based on task dependency graph (no user choice). zie-memory uses batched recall, WIP supersede, conditional micro-learning, and retro compression to stay lean.

**Tech Stack:** Markdown command files, Python hooks (pytest), zie-memory API

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| CREATE | `commands/zie-plan.md` | New planning command with approval gate |
| CREATE | `tests/unit/test_sdlc_gates.py` | All acceptance criteria tests |
| MODIFY | `commands/zie-idea.md` | Backlog-first, zie-memory READ/WRITE |
| MODIFY | `commands/zie-build.md` | Pre-flight gates, parallel agents, zie-memory micro-learning |
| MODIFY | `commands/zie-init.md` | Create backlog/ directory |
| MODIFY | `commands/zie-ship.md` | zie-memory READ step |
| MODIFY | `commands/zie-retro.md` | zie-memory all-memories READ |
| MODIFY | `hooks/intent-detect.py` | Add `plan` pattern → /zie-plan |
| MODIFY | `templates/ROADMAP.md.template` | Add Ready lane |
| MODIFY | `zie-framework/ROADMAP.md` | Add Ready lane |

Note: `/zie-fix` already has full zie-memory integration — no changes needed.

---

## Task 1: Write tests for ROADMAP Ready lane (RED)

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py` (create if not exists)

- [x] **Step 1: Write failing tests**

```python
# tests/unit/test_sdlc_gates.py

import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()


class TestROADMAPReadyLane:
    def test_template_has_ready_section(self):
        content = read("templates/ROADMAP.md.template")
        assert "## Ready" in content, "ROADMAP template must have Ready lane"

    def test_template_ready_before_now(self):
        content = read("templates/ROADMAP.md.template")
        ready_pos = content.find("## Ready")
        now_pos = content.find("## Now")
        assert ready_pos < now_pos, "Ready lane must appear before Now in template"
```

- [x] **Step 2: Run to confirm RED**

```bash
cd /Users/zie/Code/zie-framework && python3 -m pytest tests/unit/test_sdlc_gates.py::TestROADMAPReadyLane -v
```
Expected: FAIL — "Ready" not in template yet

---

## Task 2: Implement ROADMAP Ready lane (GREEN)

**Files:**
- Modify: `templates/ROADMAP.md.template`
- Modify: `zie-framework/ROADMAP.md`

- [x] **Step 1: Add Ready section to template** — insert between Next and Now:

```markdown
## Ready — Approved Plans

<!-- Plans approved by Zie, ready to build. Pull into Now when slot is free. -->

- [ ] (approved plans appear here after /zie-plan)

---

## Now — Active Sprint
```

- [x] **Step 2: Add Ready section to current ROADMAP** — same insertion, empty content:

```markdown
## Ready — Approved Plans

<!-- Plans approved by Zie, ready to build. Pull into Now when slot is free. -->

---
```

- [x] **Step 3: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestROADMAPReadyLane -v
```
Expected: PASS

---

## Task 3: Write tests for /zie-idea backlog-first + zie-memory (RED)

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py`

- [x] **Step 1: Add failing tests**

```python
class TestZieIdeaBacklogFirst:
    def test_idea_writes_to_next_not_now(self):
        content = read("commands/zie-idea.md")
        # Must mention Next section, not Now
        assert "ROADMAP Next" in content or "## Next" in content, \
            "/zie-idea must write to Next (backlog), not Now"

    def test_idea_does_not_move_to_now(self):
        content = read("commands/zie-idea.md")
        assert 'Add feature to "Now" section' not in content, \
            "/zie-idea must not move feature to Now"

    def test_idea_has_memory_recall(self):
        content = read("commands/zie-idea.md")
        assert "recall" in content.lower(), \
            "/zie-idea must recall memories before capturing idea"

    def test_idea_has_memory_store(self):
        content = read("commands/zie-idea.md")
        assert "remember" in content.lower() or "store" in content.lower(), \
            "/zie-idea must store backlog item in zie-memory"
```

- [x] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieIdeaBacklogFirst -v
```
Expected: at least 2 failures (Now reference exists, memory steps missing)

---

## Task 4: Implement /zie-idea backlog-first + zie-memory (GREEN)

**Files:**
- Modify: `commands/zie-idea.md`

- [x] **Step 1: Update Pre-flight — add zie-memory batch recall**

Add after existing step 3:
```markdown
3b. If `zie_memory_enabled=true`:
   - Single batch query: `recall project=<project> domain=<domain> limit=15`
   - Returns backlog items, shipped features, retro patterns in one call.
   - Use to detect duplicates and surface prior approaches. Cache result — do not re-query within this session.
```

- [x] **Step 2: Replace Phase 3 — change Now → Next**

Replace current step 9 (`Add feature to "Now" section`) with:
```markdown
9. Update `zie-framework/ROADMAP.md`:
   - Add feature to **Next** section only: `- [ ] <feature name> — [idea](backlog/<slug>.md)`
   - Create `zie-framework/backlog/<slug>.md` with spec summary (1-2 paragraphs).
   - Do NOT move to Now. Feature stays in backlog until /zie-plan is run.
```

- [x] **Step 3: Add zie-memory WRITE after ROADMAP update**

```markdown
9b. If `zie_memory_enabled=true`:
   - Store: `remember "Backlog item added: <slug>. Problem: <one-line summary>. Domain: <tag>." tags=[backlog, <project>, <domain>]`
```

- [x] **Step 4: Update print summary to match**

Change:
```
ROADMAP updated → Now section
```
To:
```
ROADMAP updated → Next (backlog)
Backlog item  → zie-framework/backlog/<slug>.md

<N> tasks queued. Run /zie-plan <slug> when ready to plan.
```

- [x] **Step 5: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieIdeaBacklogFirst -v
```
Expected: PASS

---

## Task 5: Write tests for /zie-plan command (RED)

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py`

- [x] **Step 1: Add failing tests**

```python
class TestZiePlanCommand:
    def test_command_file_exists(self):
        path = os.path.join(REPO_ROOT, "commands", "zie-plan.md")
        assert os.path.isfile(path), "commands/zie-plan.md must exist"

    def test_command_handles_no_args(self):
        content = read("commands/zie-plan.md")
        assert "No arguments" in content or "no args" in content.lower() \
            or "empty" in content.lower() or "list" in content.lower(), \
            "/zie-plan with no args must list backlog items"

    def test_command_has_approval_gate(self):
        content = read("commands/zie-plan.md")
        assert "approved: true" in content, \
            "/zie-plan must set approved: true in plan frontmatter"

    def test_command_moves_to_ready(self):
        content = read("commands/zie-plan.md")
        assert "Ready" in content, \
            "/zie-plan must move approved plan to Ready lane"

    def test_command_has_parallel_agents(self):
        content = read("commands/zie-plan.md")
        assert "parallel" in content.lower() and "4" in content, \
            "/zie-plan must support parallel agents capped at 4"

    def test_command_has_memory_integration(self):
        content = read("commands/zie-plan.md")
        assert "recall" in content.lower() and "remember" in content.lower(), \
            "/zie-plan must have zie-memory READ and WRITE steps"
```

- [x] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZiePlanCommand -v
```
Expected: all FAIL — file doesn't exist yet

---

## Task 6: Create /zie-plan command (GREEN)

**Files:**
- Create: `commands/zie-plan.md`

- [x] **Step 1: Create the file**

```markdown
---
description: Plan a backlog item — draft implementation plan, present for approval, move to Ready lane.
argument-hint: "[slug...] — one or more backlog item slugs (e.g. zie-plan feature-x feature-y)"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, Agent, TaskCreate
---

# /zie-plan — Backlog → Draft Plan → Approve → Ready

Draft implementation plans for backlog items and get Zie's approval before building. Supports multiple items in parallel (max 4 agents).

## Pre-flight

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → zie_memory_enabled, superpowers_enabled.

## No arguments — list and select

3. If called with no args:
   - Read `zie-framework/ROADMAP.md` → list all Next items with index numbers.
   - If Next is empty → print "No backlog items. Run /zie-idea first." and stop.
   - Ask: "Which items to plan? Enter numbers (e.g. 1, 3)"

## With slug(s) — draft plans

4. If `zie_memory_enabled=true` — READ (1 batch query per slug):
   - `recall project=<project> domain=<domain> tags=[shipped,retro,bug,decision] limit=20`
   - Returns approaches, pain points, ADRs, known bugs in one round-trip.
   - Bake key findings into plan as a "## Context from brain" section.
   - /zie-build will read this section — no need to re-recall domain context at build time.

5. If multiple slugs → spawn parallel agents (max 4) to draft plans simultaneously:
   - Each agent: reads `zie-framework/backlog/<slug>.md` → drafts plan → returns
   - Plans saved to `zie-framework/plans/<slug>.md` with no frontmatter yet (pending)

6. If single slug → draft plan inline.

## Approval gate (sequential, one plan at a time)

7. For each drafted plan:
   - Display plan to Zie.
   - Ask: "Approve this plan? (yes / re-draft / drop back to Next)"
   - **yes** → add frontmatter to plan file:
     ```yaml
     ---
     approved: true
     approved_at: YYYY-MM-DD
     backlog: backlog/<slug>.md
     ---
     ```
     Move item in `zie-framework/ROADMAP.md` from Next → Ready:
     `- [ ] <feature name> — [plan](plans/<slug>.md) ✓ approved`
   - **re-draft** → revise plan and re-present (keeps pending state)
   - **drop** → leave item in Next unchanged, skip this plan

8. If `zie_memory_enabled=true` — WRITE after approval:
   - `remember "Plan approved: <feature>. Tasks: N. Complexity: <S|M|L>. Key decisions: [<d1>]." tags=[plan, <project>, <domain>]`

## Print summary

9. Print:
   ```
   Plans processed: <N>

   Approved → Ready : <list of approved slugs>
   Re-drafted       : <list if any>
   Dropped → Next   : <list if any>

   Next: Run /zie-build to start building.
   ```

## Notes
- Plan files live at `zie-framework/plans/<slug>.md`
- Pending plan = no `approved` key in frontmatter
- Approved plan = `approved: true` + `approved_at` in frontmatter
- Max 4 parallel agents when multiple slugs provided
- Rejection path: re-draft (stays pending) or drop (returns to Next)
```

- [x] **Step 2: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZiePlanCommand -v
```
Expected: PASS

---

## Task 7: Write tests for /zie-build gates (RED)

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py`

- [x] **Step 1: Add failing tests**

```python
class TestZieBuildGates:
    def test_build_checks_wip_limit(self):
        content = read("commands/zie-build.md")
        assert "Now" in content and ("occupied" in content or "WIP" in content or "finish" in content.lower()), \
            "/zie-build must check WIP=1 (Now occupied) before proceeding"

    def test_build_checks_approved_plan(self):
        content = read("commands/zie-build.md")
        assert "approved: true" in content, \
            "/zie-build must check for approved: true in plan frontmatter"

    def test_build_has_auto_fallback(self):
        content = read("commands/zie-build.md")
        assert "auto" in content.lower() and "zie-plan" in content, \
            "/zie-build must auto-fallback to /zie-plan when no approved plan"

    def test_build_has_parallel_agents(self):
        content = read("commands/zie-build.md")
        assert "parallel" in content.lower() and "4" in content, \
            "/zie-build must support parallel agents capped at 4"

    def test_build_has_depends_on(self):
        content = read("commands/zie-build.md")
        assert "depends_on" in content, \
            "/zie-build must parse depends_on for task dependency ordering"

    def test_build_has_micro_learning(self):
        content = read("commands/zie-build.md")
        assert "micro" in content.lower() or "build-learning" in content, \
            "/zie-build must store micro-learnings per task in zie-memory"
```

- [x] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieBuildGates -v
```
Expected: multiple failures — current /zie-build missing these

---

## Task 8: Implement /zie-build gates + parallel + zie-memory (GREEN)

**Files:**
- Modify: `commands/zie-build.md`

- [x] **Step 1: Replace Pre-flight steps 2-3 with gate sequence**

Replace current steps 2-3 with:
```markdown
2. **Gate 1 — WIP check**: Read `zie-framework/ROADMAP.md` → check Now lane.
   - If Now is occupied → print "Now: `<current>` in progress. Finish it or run /zie-ship." and STOP.

3. **Gate 2 — Approved plan check**: Find active item in Ready lane.
   - If Ready is empty → auto-fallback: print "[zie-build] No approved plan. Running /zie-plan first..."
     → run `/zie-plan` (show Next list, Zie selects) → get approval → continue.
   - If Next is also empty during fallback → print "No backlog items. Run /zie-idea first." and STOP.
   - Read plan file → check frontmatter for `approved: true`.
   - If `approved: true` absent → treat as unapproved → trigger auto-fallback above.

4. Pull first Ready item → move to Now in ROADMAP.md.
5. Read `zie-framework/.config` → project_type, test_runner.
6. If `zie_memory_enabled=true` (resume only — domain context already in plan):
   - `recall project=<project> tags=[wip] feature=<slug> limit=1`
   - Read plan's "## Context from brain" section for domain context.
   - Do NOT re-recall domain patterns — /zie-plan already baked them into the plan.
```

- [x] **Step 2: Add depends_on parsing + parallel agent spawning before task loop**

Add after pre-flight:
```markdown
### Dependency resolution

Before starting tasks:
- Parse all tasks in plan for `<!-- depends_on: T1, T2 -->` comments
- Group tasks with no depends_on → **independent** (can run in parallel)
- Tasks with depends_on → **dependent** (run after blocking tasks complete)
- Spawn min(independent_count, 4) parallel agents for independent tasks
- If 0 independent tasks → execute all sequentially in dependency order
```

- [x] **Step 3: Add zie-memory WIP checkpoint with supersede** — add to step 12:

```markdown
12. Brain checkpoint (every 5 tasks or on natural stopping point):
    If `zie_memory_enabled=true`:
    - `remember "WIP: <feature> — T<N>/<total> done." tags=[wip, <project>, <feature-slug>] supersedes=[wip, <project>, <feature-slug>]`
    - supersedes replaces previous WIP memory for this feature — no duplicates.
```

- [x] **Step 4: Add conditional micro-learning** — add to step 11 (mark task complete):

```markdown
11b. If `zie_memory_enabled=true` AND task had notable friction (took longer than expected, unexpected complexity):
    - `remember "Task harder than estimated: <why>. Next time: <tip>." tags=[build-learning, <project>, <domain>]`
    - Skip this write if task went smoothly — only capture signal, not noise.
```

- [x] **Step 4: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieBuildGates -v
```
Expected: PASS

---

## Task 9: Write tests for intent-detect plan pattern (RED)

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py`

- [x] **Step 1: Add failing tests**

```python
import subprocess, json, sys

class TestIntentDetectPlan:
    def test_plan_pattern_in_code(self):
        content = read("hooks/intent-detect.py")
        assert '"plan"' in content or "'plan'" in content, \
            "intent-detect.py must have a plan category"

    def test_plan_suggestion_maps_to_zie_plan(self):
        content = read("hooks/intent-detect.py")
        assert "/zie-plan" in content, \
            "intent-detect.py must suggest /zie-plan"

    def test_plan_intent_detected_thai(self):
        """Test that Thai planning phrases trigger plan intent."""
        hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
        # Simulate hook input
        event = {"prompt": "อยากวางแผน feature ใหม่"}
        env = {**os.environ, "CLAUDE_CWD": REPO_ROOT}
        result = subprocess.run(
            [sys.executable, hook],
            input=json.dumps(event),
            capture_output=True, text=True, env=env
        )
        assert "/zie-plan" in result.stdout, \
            f"Thai planning phrase should trigger /zie-plan, got: {result.stdout!r}"
```

- [x] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestIntentDetectPlan -v
```
Expected: all FAIL

---

## Task 10: Implement intent-detect.py plan pattern (GREEN)

**Files:**
- Modify: `hooks/intent-detect.py`

- [x] **Step 1: Add plan to PATTERNS dict** — insert after `"idea"` block:

```python
"plan": [
    r"\bplan\b", r"วางแผน", r"อยากวางแผน", r"เลือก.*backlog",
    r"หยิบ.*backlog", r"plan.*feature", r"ready.*to.*plan",
    r"zie.?plan",
],
```

- [x] **Step 2: Add to SUGGESTIONS dict**:

```python
"plan": "/zie-plan",
```

- [x] **Step 3: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestIntentDetectPlan -v
```
Expected: PASS

---

## Task 11: Write tests for /zie-init backlog/ + zie-ship/retro memory (RED)

**Files:**
- Modify: `tests/unit/test_sdlc_gates.py`

- [x] **Step 1: Add failing tests**

```python
class TestZieInitBacklog:
    def test_init_creates_backlog_dir(self):
        content = read("commands/zie-init.md")
        assert "backlog" in content, \
            "/zie-init must create zie-framework/backlog/ directory"

class TestZieShipMemory:
    def test_ship_reads_wip_before_write(self):
        content = read("commands/zie-ship.md")
        assert "wip" in content.lower() or "recall" in content.lower(), \
            "/zie-ship must READ WIP checkpoint before writing ship memory"

class TestZieRetroMemory:
    def test_retro_recalls_all_since_last(self):
        content = read("commands/zie-retro.md")
        assert "since last" in content.lower() or "all memories" in content.lower() \
            or "recent" in content.lower(), \
            "/zie-retro must recall all memories since last retro"
```

- [x] **Step 2: Run to confirm RED**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieInitBacklog tests/unit/test_sdlc_gates.py::TestZieShipMemory tests/unit/test_sdlc_gates.py::TestZieRetroMemory -v
```
Expected: some failures

---

## Task 12: Implement /zie-init backlog/ + /zie-ship + /zie-retro (GREEN)

**Files:**
- Modify: `commands/zie-init.md`
- Modify: `commands/zie-ship.md`
- Modify: `commands/zie-retro.md`

- [x] **Step 1: Add backlog/ creation to /zie-init** — insert as new step after VERSION step:

```markdown
8. **Create `zie-framework/backlog/`** directory:
   - If not exists: create directory with `.gitkeep` file.
   - This is where /zie-idea stores backlog item descriptions.
```

Renumber subsequent steps accordingly.

- [x] **Step 2: Add READ step to /zie-ship (1 batch query)**:

```markdown
10b. If `zie_memory_enabled=true` — READ before writing ship memory:
   - `recall project=<project> tags=[wip, plan] feature=<slug> limit=5`
   - Single query returns WIP notes + plan estimate → compute actual vs estimated complexity.
```

- [x] **Step 3: Enhance /zie-retro — batch recall + compress + forget**:

Replace current step 4 with:
```markdown
4. If `zie_memory_enabled=true`:
   - Single batch query: `recall project=<project> since=<last_retro_date> limit=50`
   - Returns all: shipped, build-learnings, bugs, WIPs, plans since last retro.
   - Synthesize recurring patterns from build-learnings.
   - Store compressed summary: `remember "Pattern: <X> — seen N times. Fix: <Y>." tags=[retro-learning, <project>]`
   - Forget individual build-learning memories (replaced by summary — keeps brain lean).
```

- [x] **Step 4: Run tests to confirm GREEN**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py::TestZieInitBacklog tests/unit/test_sdlc_gates.py::TestZieShipMemory tests/unit/test_sdlc_gates.py::TestZieRetroMemory -v
```
Expected: PASS

---

## Task 13: Full test suite (all acceptance criteria)

- [x] **Step 1: Run all tests**

```bash
python3 -m pytest tests/unit/test_sdlc_gates.py tests/unit/test_zie_init_templates.py -v
```
Expected: all PASS

- [x] **Step 2: Run full suite**

```bash
make test-unit
```
Expected: all PASS, no regressions

- [x] **Step 3: Update plan file — mark all tasks complete**

Mark all tasks `[x]` in this file.

- [x] **Step 4: Update ROADMAP**

Move SDLC gate enforcement item from Now → Done with date.

---

## Acceptance Criteria Mapping

| AC | Covered by Task |
|----|----------------|
| AC1: /zie-idea → Next only | T3, T4 |
| AC2: /zie-plan no-args lists Next | T5, T6 |
| AC3: /zie-plan sets approved: true | T5, T6 |
| AC4: /zie-build checks approved: true | T7, T8 |
| Memory: batch recall (1 query per command) | T4, T6, T8, T12 |
| Memory: WIP supersede (no duplicate WIPs) | T8 |
| Memory: conditional micro-learning (friction only) | T8 |
| Memory: retro compression + forget build-learnings | T12 |
| Memory: context handoff plan→build (no re-recall) | T6, T8 |
| AC5: /zie-build blocks if Now occupied | T7, T8 |
| AC6: /zie-build auto-fallback | T7, T8 |
| AC7: max 4 parallel agents | T5, T6, T7, T8 |
| AC8: 0 independent tasks → sequential | T7, T8 |
| AC9: ROADMAP template has Ready lane | T1, T2 |
