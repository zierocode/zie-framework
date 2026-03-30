---
approved: true
approved_at: 2026-03-30
backlog: backlog/parallel-release-gates.md
---

# Parallel Release Gates — Design Spec

**Problem:** `/zie-release` and `/zie-retro` run quality checks and agents sequentially after their blocking prerequisites, adding unnecessary wall-clock time even though subsequent gates/agents have no data dependencies on each other.

**Approach:** After Gate 1 (unit tests) passes in `/zie-release`, spawn Gates 2–4 (integration, e2e, visual) plus a pre-Gate-1 docs-sync-check as parallel agents instead of sequential bash calls. Similarly, fix `/zie-retro` to launch ADR-write and ROADMAP-update agents truly simultaneously using `run_in_background=True` (not fallback sequential execution). Use general-purpose agent type for all parallel work to avoid plugin availability issues.

**Components:**
- `commands/zie-release.md` — restructure quality check flow: move docs-sync-check before Gate 1, spawn Gates 2–4 as parallel Agent() calls after Gate 1 passes, collect all results before version bump
- `commands/zie-retro.md` — fix concurrent Agent() invocations to use `run_in_background=True` correctly, upgrade to general-purpose agent type

**Data Flow:**

1. **Pre-Gate-1 background check** — before running Gate 1 (unit tests), spawn `Agent(subagent_type="general-purpose", run_in_background=True)` with `zie-framework:docs-sync-check` skill invocation to read files and check CLAUDE.md/README.md sync in the background.

2. **Gate 1 (unit tests)** — `make test-unit` runs synchronously and blocks all downstream gates. Must exit 0 to proceed.

3. **Upon Gate 1 pass** — immediately spawn three parallel Agent() calls (Gates 2, 3, 4) and one TaskCreate for visual check (if applicable):
   - Agent 1: Gate 2 (integration tests) — `Agent(subagent_type="general-purpose", run_in_background=True)` with prompt to run `make test-int`
   - Agent 2: Gate 3 (e2e tests, if `playwright_enabled=true`) — `Agent(subagent_type="general-purpose", run_in_background=True)` with prompt to run `make test-e2e`
   - Agent 3: Gate 4 (visual check, if `has_frontend=true`) — TaskCreate + conditional Agent (manual check or dev server verification)
   - Pre-Gate-1 docs-sync-check Agent completes concurrently

4. **Collect results** — wait for all three Agent calls (Gates 2–4) and docs-sync-check to complete. Gather ALL failures (do not stop at first failure).

5. **Failure reporting** — if any gate failed, list all failures together before stopping:
   ```
   [Gate X] FAILED: <reason>
   [Gate Y] FAILED: <reason>
   ```
   Stop after collecting all results.

6. **Success path** — if all gates pass, proceed to version bump with collected results.

**For `/zie-retro`:**

1. After building compact JSON summary, invoke both agents with `run_in_background=True` in the same message (two Agent tool calls):
   ```python
   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Write ADRs: {decisions_json}")
   Agent(subagent_type="general-purpose", run_in_background=True, prompt="Update ROADMAP Done section: {shipped_items}")
   ```

2. Wait for both tasks to complete before proceeding to brain storage.

**Edge Cases:**

1. **docs-sync-check starts before Gate 1 but completes after** — collect its result when joining all results; if stale docs found, apply updates before version bump.
2. **One gate passes, two fail** — report all two failures; stop before version bump.
3. **Gate Agent spawn fails** — fallback to sequential bash execution for that gate (graceful degradation per ADR-002).
4. **Visual check (Gate 4) requires manual confirmation** — TaskCreate prompts user inline; do not wait asynchronously.
5. **playwright_enabled=false and has_frontend=true** — Gate 4 requires manual dev server check; spawn as TaskCreate, not Agent.
6. **No integration tests exist** — Gate 2 can exit 0 safely; do not stop.
7. **Parallel task collision** — Gates 2–4 write to different test output paths (via pytest ini); no write conflicts.

**Out of Scope:**

- Changing gate logic, pass/fail conditions, or what each gate checks
- Parallelizing Gate 1 (unit tests) — remains blocking prerequisite
- Parallelizing unit + integration (shared test environment — can't safely parallelize)
- Changing version bump, CHANGELOG, or ROADMAP update logic
- Changing which agents are used for ADR/ROADMAP writes (only execution order changes)
