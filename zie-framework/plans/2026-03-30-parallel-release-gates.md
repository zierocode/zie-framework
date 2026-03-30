---
approved: true
approved_at: 2026-03-30
backlog: backlog/parallel-release-gates.md
spec: specs/2026-03-30-parallel-release-gates-design.md
---

# Plan: Parallel Release Gates

## Goal
Reduce release wall-clock time by executing Gates 2–4 (integration, e2e, visual) and docs-sync-check in parallel after Gate 1 passes, and fix `/zie-retro` to launch ADR-write and ROADMAP-update agents truly simultaneously using `run_in_background=True` with general-purpose agent type.

## Architecture
- **Execution model:** Gate 1 (unit tests) blocks. Upon Gate 1 pass, spawn Gates 2–4 as parallel `Agent(subagent_type="general-purpose", run_in_background=True)` calls with full inline prompts.
- **Pre-Gate-1 background:** docs-sync-check spawns before Gate 1, completes concurrently with unit tests.
- **Failure collection:** Wait for all parallel gates to complete, collect all failures together, report before stopping.
- **Rollback:** If any gate fails, stop before version bump; print all failures together.

## Tech Stack
- **Agent tool:** `Agent(subagent_type="general-purpose", run_in_background=True)` for all parallel work
- **Fallback:** Sequential bash execution if Agent unavailable (graceful degradation)
- **Test framework:** pytest (unchanged); Gates 2–4 use separate pytest ini files to avoid write conflicts

## File Map

| File | Responsibility | Type |
|------|---|---|
| `commands/zie-release.md` | Restructure quality check flow: move docs-sync-check before Gate 1, spawn Gates 2–4 in parallel after Gate 1 passes, collect results | Modify |
| `commands/zie-retro.md` | Fix concurrent Agent invocations to use `run_in_background=True` correctly, upgrade to general-purpose agent type | Modify |
| `tests/commands/test_zie_release_parallel_gates.py` | Test parallel gate spawning and failure collection | Create |
| `tests/commands/test_zie_retro_parallel_agents.py` | Test parallel ADR + ROADMAP agents | Create |

---

## Task 1 — Restructure `/zie-release` Commands File: Add Pre-Gate-1 Docs-Sync and Parallel Gate 2–4

<!-- depends_on: none -->

**File:** `commands/zie-release.md`
**Test:** `tests/commands/test_zie_release_parallel_gates.py` (new)

**RED:**
1. Write test asserting docs-sync-check Agent spawns before unit tests run (mock Agent, capture spawn timestamp)
2. Write test asserting Gates 2, 3, 4 Agent calls spawn simultaneously after Gate 1 passes (all within 1s)
3. Write test asserting all three gate results collected before version bump (no stop at first failure)

**GREEN:**
1. Add new "Pre-Gate-1 Background Check" section BEFORE unit tests:
   ```markdown
   ### Pre-Gate-1 Background Check

   **TaskCreate:**
   ```python
   TaskCreate(subject="Check docs sync", description="Check CLAUDE.md/README.md against changed files", activeForm="Checking docs sync")
   ```

   **Spawn docs-sync-check Agent:**
   ```python
   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Check CLAUDE.md and README.md for staleness. Read current files and compare against active commands, skills, hooks on disk. Report: [docs-sync] PASSED or [docs-sync] FAILED: <what's stale>")
   ```
   ```

2. Keep Gate 1 (unit tests) as blocking prerequisite.

3. After Gate 1 passes, add "Spawn Parallel Gates 2–4" section:
   ```markdown
   ### Spawn Parallel Gates 2–4

   **Upon Gate 1 success, immediately spawn three Agents:**
   ```python
   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Run integration tests: execute `make test-int`. Report result: [Gate 2] PASSED or [Gate 2] FAILED: <reason>")

   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Run e2e tests (if enabled): check playwright_enabled in zie-framework/.config. If true, execute `make test-e2e`. If false, skip. Report: [Gate 3] PASSED or [Gate 3] SKIPPED or [Gate 3] FAILED: <reason>")

   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Visual check (if applicable): check has_frontend and playwright_enabled in zie-framework/.config. If has_frontend=true and playwright_enabled=false, start dev server and verify key pages load without console errors. Report: [Gate 4] PASSED or [Gate 4] SKIPPED or [Gate 4] FAILED: <reason>")
   ```
   ```

4. Add "Collect Parallel Gate Results" section after gate spawning:
   ```markdown
   ### Collect Parallel Gate Results

   Wait for all three gate Agents to complete. Collect results from each (do not stop at first failure).

   - If all three pass (or skip) → print "Gates 2, 3, 4 PASSED" → continue
   - If any fail → print all failures together, then STOP before version bump:
     ```
     [Gate 2] FAILED: integration tests failed
     [Gate 3] FAILED: e2e tests timed out
     ```
   - Also wait for and collect docs-sync-check result (pre-Gate-1 Agent)
   - If docs found stale, update CLAUDE.md/README.md now before version bump
   ```

5. Update existing "Quality Checks" section:
   - Remove the docs-sync-check Agent (now runs pre-Gate-1)
   - Keep TODOs/secrets bash scan (runs in parallel with Gate 2–4)

6. Update "รวมผลลัพธ์ Quality Forks" section to note docs-sync-check results already collected

**AC:**
- [ ] docs-sync-check Agent spawns before unit tests (verified by test)
- [ ] Gates 2, 3, 4 Agents spawn within 1s of each other after Gate 1 passes (verified by test)
- [ ] All three gate results collected before proceeding or stopping (verified by test)
- [ ] If one gate fails, all failures listed together before stopping (verified by test)
- [ ] docs-sync-check result also collected and stale docs updated if needed
- [ ] All Agent calls use `subagent_type="general-purpose"` and `run_in_background=True`
- [ ] All prompts are full inline text (no skill references)
- [ ] `make test-unit` passes with new tests

---

## Task 2 — Restructure `/zie-retro` to Launch ADR-Write and ROADMAP-Update Agents Simultaneously

<!-- depends_on: Task 1 -->

**File:** `commands/zie-retro.md`
**Test:** `tests/commands/test_zie_retro_parallel_agents.py` (new)

**RED:**
1. Write test asserting ADR-write and ROADMAP-update Agents spawn in same message (both Agent calls detected)
2. Write test asserting both use `run_in_background=True` and `subagent_type="general-purpose"`
3. Write test asserting both include full inline prompts (no skill references)

**GREEN:**
1. Locate "บันทึก ADRs + อัปเดต ROADMAP (parallel)" section in `/zie-retro`

2. Replace current sequential implementation with true parallel execution:
   ```markdown
   ### บันทึก ADRs + อัปเดต ROADMAP (parallel)

   **Invoke both Agents simultaneously in one message block:**
   ```python
   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Write ADRs for decisions made this session. For each decision in {decisions_json}: create file zie-framework/decisions/ADR-<NNN>-<slug>.md with title, status, context, decision, consequences sections. Next ADR number: {next_adr_n}. Print [ADR N/total] for each file created.")

   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Update ROADMAP Done section. Read zie-framework/ROADMAP.md. Find ## Done section. Move shipped items from ## Now to Done with date (YYYY-MM-DD) and version tag. Items: {shipped_items}. Replace ## Done block (from heading to next --- separator or EOF). Save updated file.")
   ```
   ```

3. Update completion handling section:
   ```markdown
   Await both Agents to complete. Collect and print results from both.
   - If either Agent fails → print error and skip brain store (non-blocking)
   - If both succeed → continue to brain store step
   ```

4. Update fallback comments to note graceful degradation if Agent unavailable

**AC:**
- [ ] ADR-write and ROADMAP-update Agents spawn in same message (simultaneously) (verified by test)
- [ ] Both use `subagent_type="general-purpose"` (verified by test)
- [ ] Both use `run_in_background=True` (verified by test)
- [ ] Both include full inline prompts, no skill references (verified by test)
- [ ] Results collected before proceeding to brain store
- [ ] If either fails, error printed and brain store skipped (non-blocking)
- [ ] `make test-unit` passes with new tests

---

## Task 3 — Write Comprehensive Test Suite for Parallel Execution

<!-- depends_on: Task 1, Task 2 -->

**File:** `tests/commands/test_zie_release_parallel_gates.py` (create new), `tests/commands/test_zie_retro_parallel_agents.py` (create new)
**Test:** Unit tests using mocks + integration tests with live agents

**RED:**
For `test_zie_release_parallel_gates.py`:
1. Test parallel gate spawn timing: mock Agent tool, capture all spawn timestamps, assert all within 1s
2. Test gate failure collection: simulate one gate pass, two fail; assert all results collected before stop
3. Test agent type validation: assert all Agents use `subagent_type="general-purpose"`

For `test_zie_retro_parallel_agents.py`:
1. Test parallel agent spawn timing: mock Agent tool, assert both spawn within 1s
2. Test agent type validation: assert both use `subagent_type="general-purpose"` and `run_in_background=True`
3. Test prompt format: assert prompts are full inline text, not skill references

**GREEN:**
1. Create `tests/commands/test_zie_release_parallel_gates.py`:
   ```python
   import pytest
   from unittest.mock import Mock, patch, call
   import time

   def test_gate_2_3_4_spawn_simultaneously():
       """Verify Gates 2, 3, 4 Agent calls spawn within 1s of each other."""
       # Mock Agent tool, capture spawn timestamps
       # Assert all three within 1s window

   def test_collect_all_gate_failures_before_stopping():
       """Simulate Gate 2 pass, Gate 3 fail, Gate 4 pass. Verify all results collected."""
       # Mock gate results, verify collection before stop decision

   def test_gate_agents_use_general_purpose_type():
       """Verify all gate Agents use subagent_type='general-purpose'."""
       # Inspect Agent calls, assert type on each

   def test_docs_sync_check_spawns_before_gate_1():
       """Verify docs-sync-check Agent spawns before unit tests."""
       # Mock Agent and bash, verify Agent spawn before make test-unit

   def test_agent_run_in_background_true():
       """Verify all parallel Agents use run_in_background=True."""
       # Inspect Agent calls, assert flag on each
   ```

2. Create `tests/commands/test_zie_retro_parallel_agents.py`:
   ```python
   import pytest
   from unittest.mock import Mock, patch, call
   import time

   def test_adr_roadmap_agents_spawn_simultaneously():
       """Verify ADR-write and ROADMAP-update Agents spawn in same message."""
       # Mock Agent tool, capture spawn within same call block
       # Assert both within 1s

   def test_retro_agents_use_general_purpose_type():
       """Verify both retro Agents use subagent_type='general-purpose'."""
       # Inspect Agent calls, assert type on both

   def test_retro_agents_run_in_background_true():
       """Verify both retro Agents use run_in_background=True."""
       # Inspect Agent calls, assert flag on both

   def test_retro_prompts_no_skill_references():
       """Verify ADR and ROADMAP prompts are full inline, not skill refs."""
       # Inspect prompts, assert no "zie-framework:" references
   ```

3. Update `tests/commands/conftest.py` or create shared mocks for Agent tool

**AC:**
- [ ] All unit tests pass with `make test-unit`
- [ ] All assertions validate timing (spawn within 1s)
- [ ] All assertions validate agent type (`general-purpose`)
- [ ] All assertions validate `run_in_background=True` flag
- [ ] All assertions validate inline prompts (no skill refs)
- [ ] Tests cover edge cases: one gate fails, two fail, all pass
- [ ] Tests cover graceful degradation if Agent unavailable
- [ ] Code coverage > 80% for modified sections

---

## Fallback & Error Handling

**Edge Case 1: Agent tool unavailable**
- If Agent spawn fails → print `[zie-framework] parallel gates unavailable — falling back to sequential bash execution`
- Fall back to sequential: `make test-int` → `make test-e2e` → visual check
- Release continues; not blocked

**Edge Case 2: One gate passes, two fail**
- Collect all results
- Print:
  ```
  [Gate 2] PASSED
  [Gate 3] FAILED: e2e tests timed out
  [Gate 4] FAILED: visual check manual confirmation not received
  ```
- STOP before version bump

**Edge Case 3: docs-sync-check runs after Gate 1 finishes**
- If docs-sync-check still running when Gate 1 completes → wait for completion in "Collect Parallel Gate Results"
- Apply stale docs updates before version bump if needed
- Non-critical: does not block release if fails

**Edge Case 4: Visual check requires manual confirmation**
- If `has_frontend=true` and `playwright_enabled=false` → Gate 4 is manual TaskCreate, not Agent
- Prompt user: "Visual check: confirm pages load without errors (yes/no)"
- If yes → [Gate 4] PASSED
- If no → [Gate 4] FAILED (stop before version bump)

---

## Verification Checklist

- [ ] `commands/zie-release.md` loads without syntax errors
- [ ] `commands/zie-retro.md` loads without syntax errors
- [ ] All Agent calls use `subagent_type="general-purpose"`
- [ ] All parallel Agent calls use `run_in_background=True`
- [ ] No Agent calls reference zie-framework-specific agent types (except fallback comments)
- [ ] All prompts are full inline text (no skill references like `zie-framework:docs-sync-check`)
- [ ] `make test-unit` passes (all new tests included)
- [ ] `make test-ci` passes (coverage gate satisfied)
- [ ] Manual release test: `/zie-release` runs, Gates 2–4 spawn simultaneously, all results collected before version bump
- [ ] Manual retro test: `/zie-retro` runs, ADR-write and ROADMAP-update Agents spawn simultaneously
