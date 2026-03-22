---
approved: true
approved_at: 2026-03-22
backlog: backlog/fork-superpowers-skills.md
---

# Fork Superpowers Skills — Implementation Plan

> **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.

**Goal:** Fork brainstorming, writing-plans, systematic-debugging, and verification skills from superpowers into zie-framework/skills/ so zie-framework is a self-contained SDLC framework with native zie-memory integration and no external plugin dependency.

**Architecture:** Each forked skill becomes a `zie-framework/skills/<name>/SKILL.md` file adapted to use zie-framework paths (`zie-framework/specs/`, `zie-framework/plans/`) natively, with zie-memory batch recall/write instructions embedded at every relevant step. Once all four skills exist, each command that previously called `Skill(superpowers:*)` is updated to call `Skill(zie-framework:*)` instead, and the override notes (directory overrides, commit overrides) are removed since the native skills already encode the right behavior.

**Tech Stack:** Markdown skill files (SKILL.md), Python hooks (pytest)

---

## Context from brain

_No prior brain recall available for this session — context gathered from reading source files directly._

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `skills/spec-design/SKILL.md` | Fork of superpowers brainstorming — zie-memory aware, uses zie-framework/specs/ paths |
| Create | `skills/write-plan/SKILL.md` | Fork of superpowers writing-plans — saves to zie-framework/plans/, no auto-commit |
| Create | `skills/debug/SKILL.md` | Fork of superpowers systematic-debugging — references zie-framework:tdd-loop, zie-memory bug recall |
| Create | `skills/verify/SKILL.md` | Fork of superpowers verification-before-completion — zie-framework branded, no changes to core logic |
| Modify | `commands/zie-idea.md` | Replace `Skill(superpowers:brainstorming)` + `Skill(superpowers:writing-plans)` with zie-framework equivalents; remove directory/commit overrides |
| Modify | `commands/zie-build.md` | Replace `Skill(superpowers:test-driven-development)` with `Skill(zie-framework:tdd-loop)`; replace `Skill(superpowers:systematic-debugging)` with zie-framework equivalent |
| Modify | `commands/zie-fix.md` | Replace `Skill(superpowers:systematic-debugging)` and `Skill(superpowers:verification-before-completion)` with zie-framework equivalents |
| Modify | `commands/zie-ship.md` | Replace `Skill(superpowers:verification-before-completion)` and `Skill(superpowers:requesting-code-review)` references with zie-framework equivalents or inline steps |
| Create | `tests/unit/test_fork_superpowers_skills.py` | All tests for this feature — file existence, content assertions, command reference assertions |

---

## Task 1: Test scaffolding — skill file existence (RED)

**Files:**
- Create: `tests/unit/test_fork_superpowers_skills.py`

- [ ] **Step 1: Write failing tests asserting skill files exist**

```python
# tests/unit/test_fork_superpowers_skills.py
import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def skill_path(name):
    return os.path.join(REPO_ROOT, "skills", name, "SKILL.md")

def read(rel_path):
    with open(os.path.join(REPO_ROOT, rel_path)) as f:
        return f.read()

class TestSkillFilesExist:
    def test_brainstorming_skill_exists(self):
        assert os.path.exists(skill_path("spec-design")), \
            "skills/spec-design/SKILL.md must exist"

    def test_writing_plans_skill_exists(self):
        assert os.path.exists(skill_path("write-plan")), \
            "skills/write-plan/SKILL.md must exist"

    def test_systematic_debugging_skill_exists(self):
        assert os.path.exists(skill_path("debug")), \
            "skills/debug/SKILL.md must exist"

    def test_verification_skill_exists(self):
        assert os.path.exists(skill_path("verify")), \
            "skills/verify/SKILL.md must exist"
```

- [ ] **Step 2: Run to confirm RED**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -A5 "TestSkillFilesExist"
```

Expected: 4 failures — `SKILL.md` files do not exist yet.

---

## Task 2: Fork `spec-design` skill (GREEN)
<!-- depends_on: T1 -->

**Files:**
- Create: `skills/spec-design/SKILL.md`

- [ ] **Step 1: Create `skills/spec-design/` directory and write SKILL.md**

Content requirements:
- Frontmatter: `name: brainstorming`, `description:` matching superpowers version
- Replace all `docs/superpowers/specs/` path references with `zie-framework/specs/`
- Remove "commit the design document" instruction (zie-framework never auto-commits)
- Remove the visual companion browser section (not applicable)
- Add zie-memory integration block after "Explore project context" step:
  ```
  ## zie-memory Pre-flight
  If zie_memory_enabled=true — READ (1 batch query):
    recall project=<project> domain=<domain> limit=15
    → returns: past backlog items, shipped features, retro patterns
    → use to: detect duplicates, surface prior approaches
    → cache result — do not re-query within this session
  ```
- Add zie-memory WRITE block after spec is written:
  ```
  If zie_memory_enabled=true — WRITE:
    "Backlog: <slug>. Problem: <why>. Domain: <domain>."
    tags: [backlog, <project>, <domain>]
  ```
- Remove reference to `spec-document-reviewer subagent` dispatching (superpowers internal)
- Keep the core brainstorming flow: clarifying questions → approaches → design sections → approval → write spec
- Terminal state: invoke `Skill(zie-framework:write-plan)` (not superpowers)

- [ ] **Step 2: Run tests to confirm `test_brainstorming_skill_exists` is GREEN**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -E "PASSED|FAILED" | grep brainstorming
```

---

## Task 3: Fork `write-plan` skill (GREEN)
<!-- depends_on: T1 -->

**Files:**
- Create: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Create `skills/write-plan/` directory and write SKILL.md**

Content requirements:
- Frontmatter: `name: writing-plans`, `description:` matching superpowers version
- Replace plan save path `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.md` with `zie-framework/plans/YYYY-MM-DD-<feature-name>.md`
- Update plan document header block — replace superpowers header with zie-framework equivalent:
  ```
  > **For agentic workers:** Use /zie-build to implement this plan task-by-task with TDD RED/GREEN/REFACTOR loop.
  ```
- Remove `superpowers:subagent-driven-development` and `superpowers:executing-plans` references in Execution Handoff section — replace with: "Hand off to /zie-build."
- Remove "Commit" steps from task structure template (zie-framework does not auto-commit per task)
- Remove plan-document-reviewer subagent dispatch (superpowers internal)
- Add `## Context from brain` section placeholder to the plan document header template:
  ```
  ## Context from brain
  _Populated by /zie-plan recall query — key past patterns, pain points, ADRs._
  ```
- Add `depends_on` task comment syntax documentation:
  ```
  ## Dependency Markers
  Tasks with no dependencies run in parallel (zie-build spawns up to 4 agents).
  To declare a dependency, add after the task heading:
    <!-- depends_on: T1, T2 -->
  ```
- Keep all TDD task structure format, file map, bite-sized steps

- [ ] **Step 2: Run tests to confirm `test_writing_plans_skill_exists` is GREEN**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -E "PASSED|FAILED" | grep writing
```

---

## Task 4: Fork `debug` skill (GREEN)
<!-- depends_on: T1 -->

**Files:**
- Create: `skills/debug/SKILL.md`

- [ ] **Step 1: Create `skills/debug/` directory and write SKILL.md**

Content requirements:
- Frontmatter: `name: systematic-debugging`, `description:` matching superpowers version
- Replace all `superpowers:test-driven-development` references with `zie-framework:tdd-loop`
- Replace all `superpowers:verification-before-completion` references with `zie-framework:verify`
- Add zie-memory pre-flight block at top of "When to Use" section:
  ```
  ## zie-memory Pre-flight
  If zie_memory_enabled=true — READ (1 batch query) before starting investigation:
    recall project=<project> domain=<domain> tags=[bug, build-learning] limit=10
    → detect recurring patterns, surface known fragile areas
    → cache result — do not re-query within this session
  ```
- Add zie-memory WRITE block at Phase 4 "Verify Fix" step:
  ```
  If zie_memory_enabled=true — WRITE after fix confirmed:
    "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>."
    tags: [bug, <project>, <domain>]
  ```
- Remove supporting techniques file references (`root-cause-tracing.md`, `defense-in-depth.md`, `condition-based-waiting.md`) — those are superpowers internal files; replace with inline summary of each technique
- Keep all four phases intact: Root Cause Investigation, Pattern Analysis, Hypothesis and Testing, Implementation

- [ ] **Step 2: Run tests to confirm `test_systematic_debugging_skill_exists` is GREEN**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -E "PASSED|FAILED" | grep debugging
```

---

## Task 5: Fork `verify` skill (GREEN)
<!-- depends_on: T1 -->

**Files:**
- Create: `skills/verify/SKILL.md`

- [ ] **Step 1: Create `skills/verify/` directory and write SKILL.md**

Content requirements:
- Frontmatter: `name: verification`, `description:` matching superpowers `verification-before-completion`
- Content is nearly identical to superpowers version — core logic (Iron Law, Gate Function, Common Failures, Red Flags) is preserved unchanged
- Remove the "From 24 failure memories" line — replace with: "Evidence before assertions is non-negotiable."
- Replace any `superpowers:*` skill name references with `zie-framework:*` equivalents
- No zie-memory integration needed for this skill (verification is a pure process check, not a data-recall step)

- [ ] **Step 2: Run tests to confirm `test_verification_skill_exists` is GREEN**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -E "PASSED|FAILED" | grep verification
```

---

## Task 6: Test zie-memory integration content in skills (RED)
<!-- depends_on: T2, T3, T4 -->

**Files:**
- Modify: `tests/unit/test_fork_superpowers_skills.py`

- [ ] **Step 1: Add content assertion tests**

```python
class TestSkillZieMemoryIntegration:
    def test_brainstorming_has_zie_memory_recall(self):
        content = read("skills/spec-design/SKILL.md")
        assert "recall" in content and "zie_memory_enabled" in content, \
            "brainstorming skill must include zie-memory batch recall instructions"

    def test_brainstorming_saves_to_zie_framework_specs(self):
        content = read("skills/spec-design/SKILL.md")
        assert "zie-framework/specs/" in content, \
            "brainstorming skill must save specs to zie-framework/specs/"
        assert "docs/superpowers/specs/" not in content, \
            "brainstorming skill must not reference superpowers spec path"

    def test_writing_plans_saves_to_zie_framework_plans(self):
        content = read("skills/write-plan/SKILL.md")
        assert "zie-framework/plans/" in content, \
            "writing-plans skill must save plans to zie-framework/plans/"
        assert "docs/superpowers/plans/" not in content, \
            "writing-plans skill must not reference superpowers plan path"

    def test_writing_plans_has_context_from_brain_section(self):
        content = read("skills/write-plan/SKILL.md")
        assert "Context from brain" in content, \
            "writing-plans skill must include ## Context from brain section in plan template"

    def test_writing_plans_has_depends_on_docs(self):
        content = read("skills/write-plan/SKILL.md")
        assert "depends_on" in content, \
            "writing-plans skill must document depends_on task marker syntax"

    def test_systematic_debugging_has_zie_memory_recall(self):
        content = read("skills/debug/SKILL.md")
        assert "recall" in content and "zie_memory_enabled" in content, \
            "systematic-debugging skill must include zie-memory recall instructions"

    def test_systematic_debugging_no_superpowers_refs(self):
        content = read("skills/debug/SKILL.md")
        assert "superpowers:" not in content, \
            "systematic-debugging must not reference superpowers: skill names"

    def test_brainstorming_no_superpowers_refs(self):
        content = read("skills/spec-design/SKILL.md")
        assert "superpowers:" not in content, \
            "brainstorming skill must not reference superpowers: skill names"

    def test_writing_plans_no_superpowers_refs(self):
        content = read("skills/write-plan/SKILL.md")
        assert "superpowers:" not in content, \
            "writing-plans skill must not reference superpowers: skill names"
```

- [ ] **Step 2: Run to confirm RED (tests fail before command updates)**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -A3 "TestSkillZieMemoryIntegration"
```

Expected: failures for content assertions not yet satisfied (some may already pass if skills were written correctly in T2–T5).

---

## Task 7: Fix any skill content gaps to pass Task 6 tests (GREEN)
<!-- depends_on: T6 -->

**Files:**
- Modify: `skills/spec-design/SKILL.md` (if needed)
- Modify: `skills/write-plan/SKILL.md` (if needed)
- Modify: `skills/debug/SKILL.md` (if needed)

- [ ] **Step 1: Run full test suite and read failures**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep "FAILED"
```

- [ ] **Step 2: For each failing content assertion — open the relevant skill file and add the missing content**

Apply minimal edits only — add the missing section/phrase that the test asserts.

- [ ] **Step 3: Run tests to confirm all TestSkillZieMemoryIntegration tests GREEN**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -E "PASSED|FAILED" | grep TestSkill
```

---

## Task 8: Test commands no longer reference `superpowers:` (RED)
<!-- depends_on: T1 -->

**Files:**
- Modify: `tests/unit/test_fork_superpowers_skills.py`

- [ ] **Step 1: Add command reference tests**

```python
class TestCommandsNoSuperpowersDependency:
    def test_zie_idea_no_superpowers_skill(self):
        content = read("commands/zie-idea.md")
        assert "Skill(superpowers:" not in content, \
            "zie-idea must not call Skill(superpowers:*) after fork"

    def test_zie_build_no_superpowers_skill(self):
        content = read("commands/zie-build.md")
        assert "Skill(superpowers:" not in content, \
            "zie-build must not call Skill(superpowers:*) after fork"

    def test_zie_fix_no_superpowers_skill(self):
        content = read("commands/zie-fix.md")
        assert "Skill(superpowers:" not in content, \
            "zie-fix must not call Skill(superpowers:*) after fork"

    def test_zie_ship_no_superpowers_skill(self):
        content = read("commands/zie-ship.md")
        assert "Skill(superpowers:" not in content, \
            "zie-ship must not call Skill(superpowers:*) after fork"

    def test_zie_idea_calls_zie_framework_brainstorming(self):
        content = read("commands/zie-idea.md")
        assert "Skill(zie-framework:spec-design)" in content, \
            "zie-idea must invoke Skill(zie-framework:spec-design)"

    def test_zie_idea_calls_zie_framework_writing_plans(self):
        content = read("commands/zie-idea.md")
        assert "Skill(zie-framework:write-plan)" in content, \
            "zie-idea must invoke Skill(zie-framework:write-plan)"

    def test_zie_build_calls_zie_framework_tdd_loop(self):
        content = read("commands/zie-build.md")
        assert "Skill(zie-framework:tdd-loop)" in content, \
            "zie-build must invoke Skill(zie-framework:tdd-loop)"

    def test_zie_build_calls_zie_framework_systematic_debugging(self):
        content = read("commands/zie-build.md")
        assert "Skill(zie-framework:debug)" in content, \
            "zie-build must invoke Skill(zie-framework:debug)"

    def test_zie_fix_calls_zie_framework_systematic_debugging(self):
        content = read("commands/zie-fix.md")
        assert "Skill(zie-framework:debug)" in content, \
            "zie-fix must invoke Skill(zie-framework:debug)"

    def test_zie_fix_calls_zie_framework_verification(self):
        content = read("commands/zie-fix.md")
        assert "Skill(zie-framework:verify)" in content, \
            "zie-fix must invoke Skill(zie-framework:verify)"

    def test_zie_ship_calls_zie_framework_verification(self):
        content = read("commands/zie-ship.md")
        assert "Skill(zie-framework:verify)" in content, \
            "zie-ship must invoke Skill(zie-framework:verify)"
```

- [ ] **Step 2: Run to confirm RED**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -A3 "TestCommandsNoSuperpowersDependency"
```

Expected: all 11 tests fail — commands still reference `superpowers:`.

---

## Task 9: Update commands to use zie-framework skills (GREEN)
<!-- depends_on: T8, T2, T3, T4, T5 -->

**Files:**
- Modify: `commands/zie-idea.md`
- Modify: `commands/zie-build.md`
- Modify: `commands/zie-fix.md`
- Modify: `commands/zie-ship.md`

- [ ] **Step 1: Update `commands/zie-idea.md`**

Changes:
- Replace `Skill(superpowers:brainstorming)` with `Skill(zie-framework:spec-design)`
- Remove the `**Directory override**` note — the forked skill already saves to `zie-framework/specs/`
- Remove the `**Spec reviewer override**` note — the forked skill does not dispatch a superpowers spec reviewer
- Remove the `**Commit override**` note — the forked skill does not auto-commit
- Replace `Skill(superpowers:writing-plans)` with `Skill(zie-framework:write-plan)`
- Remove `Copy/move plan to zie-framework/plans/...` step — forked skill saves there directly
- Remove `If superpowers_enabled=true/false` branching logic for Phase 1 and Phase 2 — simplify to single path using zie-framework skills
- Keep: zie-memory pre-flight, ROADMAP update, backlog write

- [ ] **Step 2: Update `commands/zie-build.md`**

Changes:
- Replace `Skill(superpowers:test-driven-development)` with `Skill(zie-framework:tdd-loop)`
- Remove `if superpowers_enabled=true` guard — tdd-loop skill is always available natively
- Replace `Skill(superpowers:systematic-debugging)` with `Skill(zie-framework:debug)`
- Keep all other logic unchanged (gates, memory, task loop, parallel agents)

- [ ] **Step 3: Update `commands/zie-fix.md`**

Changes:
- Replace `Skill(superpowers:systematic-debugging)` with `Skill(zie-framework:debug)`
- Replace `Skill(superpowers:verification-before-completion)` with `Skill(zie-framework:verify)`
- Keep all other logic unchanged

- [ ] **Step 4: Update `commands/zie-ship.md`**

Changes:
- Replace `Skill(superpowers:verification-before-completion)` with `Skill(zie-framework:verify)`
- Replace `Skill(superpowers:requesting-code-review)` with inline instruction: "Spawn a subagent to review the diff — read the git diff output and evaluate: correctness, regressions, edge cases missed."
- Keep all other gate logic unchanged

- [ ] **Step 5: Run tests to confirm all TestCommandsNoSuperpowersDependency tests GREEN**

```bash
cd /Users/zie/Code/zie-framework && make test-unit 2>&1 | grep -E "PASSED|FAILED" | grep TestCommands
```

---

## Task 10: Full test suite GREEN + REFACTOR
<!-- depends_on: T7, T9 -->

**Files:**
- Modify: `tests/unit/test_fork_superpowers_skills.py` (cleanup only, no new tests)
- Modify: Any skill or command files needing minor cleanup

- [ ] **Step 1: Run full test suite**

```bash
cd /Users/zie/Code/zie-framework && make test-unit
```

Expected: all tests pass — existing tests (`test_sdlc_gates.py`, `test_zie_init_templates.py`) still green, all new tests green.

- [ ] **Step 2: REFACTOR — review all four forked skills for consistency**

Check across all four skill files:
- Frontmatter format consistent with existing skills (`tdd-loop`, `test-pyramid`, `retro-format`)
- No dangling references to superpowers paths or subagents
- zie-memory blocks use consistent terminology (`zie_memory_enabled`, `recall`, `remember`)
- All Skill cross-references use `zie-framework:` prefix

- [ ] **Step 3: REFACTOR — review commands for clarity**

Check in each updated command:
- No orphaned `If superpowers_enabled` guards referencing the removed branches
- No `**Directory override**` or `**Commit override**` notes remaining
- Skill invocations use the new names consistently

- [ ] **Step 4: Run full test suite one final time to confirm clean**

```bash
cd /Users/zie/Code/zie-framework && make test-unit
```

Expected: all pass, no warnings.

- [ ] **Step 5: Print summary**

```
Fork complete.

New skills:
  skills/spec-design/SKILL.md
  skills/write-plan/SKILL.md
  skills/debug/SKILL.md
  skills/verify/SKILL.md

Updated commands:
  commands/zie-idea.md   — removed superpowers:brainstorming, writing-plans + overrides
  commands/zie-build.md  — removed superpowers:test-driven-development, systematic-debugging
  commands/zie-fix.md    — removed superpowers:systematic-debugging, verification-before-completion
  commands/zie-ship.md   — removed superpowers:verification-before-completion, requesting-code-review

zie-framework is now self-contained. superpowers plugin is no longer required.
```
