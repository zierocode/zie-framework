---
approved: true
approved_at: 2026-04-15
backlog: backlog/parallel-pipeline-stages.md
---

# Parallel Pipeline Stages — Implementation Plan

**Goal:** Change sprint Phase 1 to spawn parallel background agents for each item's spec+plan pipeline, reducing wall-clock time for multi-item sprints.
**Architecture:** Replace sequential Skill calls in Phase 1 with Agent tool spawning (context: fork, run_in_background). Each agent runs spec-design → spec-review → write-plan → plan-review → approve.py independently. Concurrency cap of 4 limits token explosion. Single-item sprint falls back to Skill call (no agent overhead). ROADMAP and sprint-context.json are written once after all agents complete.
**Tech Stack:** Markdown (commands/sprint.md), no new Python code

**Risk Review:** No hidden dependencies — Agent tool is a core Claude Code feature. Ordering risk: all Phase 1 changes are in one file, so tasks must be serialized. Rollback: revert changes to sprint.md.

**ADR-058 tension:** ADR-058 moved away from Agent spawning for reviewers (polling complexity, context overhead). This plan re-introduces Agent spawning for Phase 1 spec+plan — but the use case is different: independent items processed in parallel (fire-and-collect), not per-task review polling. No deferred results or retry loops needed — each agent runs to completion and returns. ADR-058's concerns (polling, context overhead per confirm pass) don't apply to this fire-and-collect pattern.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/sprint.md` | Restructure Phase 1 for parallel Agent spawning with concurrency cap |

---

## Task 1: Restructure Phase 1 for parallel Agent spawning

<!-- depends_on: none -->

**Acceptance Criteria:**
- Phase 1 spawns one background Agent per item (up to concurrency cap of 4)
- Each agent prompt includes: backlog slug, context_bundle, autonomous instructions
- Single-item fallback: if only 1 item needs spec+plan, use Skill call (no agent spawn)
- Progress reporting: delta-only as agents complete, full table at phase end
- Agent failure: inline retry once within agent → still failing → surface to main sprint context
- Per-agent completion: .sprint-state tracks which agents have completed (so resume can skip them)
- Summary section updated: "parallel agents + inline retry"

**Files:**
- Modify: `commands/sprint.md`

- [ ] **Step 1: Read current sprint.md Phase 1 section**
  Read `commands/sprint.md` lines 78-100 to get exact text of Phase 1.

- [ ] **Step 2: Replace Phase 1 with parallel Agent spawning**
  Replace the entire PHASE 1 section (lines 78-100). The new text — use `~~~` delimiters for the agent prompt to avoid nested triple-backtick issues:

  ~~~markdown
  ## PHASE 1: SPEC ALL (Parallel Agents)

  TaskCreate subject="Phase 1/4 — Spec All"

  For `[clarity: ask]` items: ask 1 question per item first, then proceed.

  **Concurrency cap:** `min(4, number of items in needs_spec)`. Excess items queue until slots open.

  **Single-item fast path:** If only 1 item needs spec+plan, use Skill calls directly (no Agent spawn overhead):
  1. `Skill(zie-framework:spec-design, '<slug> autonomous')` → spec-review inline → approve
  2. `Skill(zie-framework:write-plan, '<slug>')` → plan-review inline → approve.py
  3. Skip to Phase 1 completion below.

  **Multi-item parallel path:** For each item in needs_spec (up to `cap` concurrent):

  Spawn background Agent with prompt:

      You are running the spec+plan pipeline for backlog item "<slug>".

      1. Invoke `Skill(zie-framework:spec-design, '<slug> autonomous')` — this writes the spec, runs spec-review inline, and auto-approves.
      2. Invoke `Skill(zie-framework:write-plan, '<slug>')` — this writes the plan.
      3. Invoke `Skill(zie-framework:plan-review)` inline — verify the plan.
         - ✅ APPROVED → run `python3 hooks/approve.py <plan-file>` via Bash
         - ❌ Issues Found → fix all issues inline → verify each fix against issue list → run approve.py
         - Any issue unfixable → return failure with details

      Context bundle is provided below. Use it directly — do not re-invoke load-context.

      <context_bundle>

  Wait for all agents to complete. As each agent returns:
  - Success → `[spec N/total] <slug> ✓` → update `.sprint-state`: add slug to `completed_phase1_items`
  - Failure → inline retry: re-spawn a single Agent for that slug. If retry also fails → `[spec N/total] <slug> ❌ <issue>` → halt sprint.

  After all Phase 1 agents (+ retries): reload ROADMAP → `roadmap_post_phase1`.
  Update ROADMAP: move all approved items from Next → Ready (single batch write, not per-agent).

  Progress: delta-only per agent; full table at phase end.

  Extract keywords per item from backlog items (Problem + Approach — top 6 terms each). Write sprint context to `.zie/sprint-context.json`:

      sprint_context = {
          "specs": {...},           # Spec content for each item (keyed by slug)
          "plans": {...},          # Plan content for each item (keyed by slug)
          "roadmap": roadmap_post_phase1,
          "keywords_per_item": {...},  # slug → keywords string for downstream load-context calls
      }

  Do NOT persist full context_bundle in JSON — downstream phases call load-context with keywords (cached).

  TaskUpdate → Phase 1/4 complete. Write `.sprint-state` with phase=2, `completed_phase1_items: [<list of completed slugs>]`.

  **Context checkpoint:** Run `/compact` to clear Phase 1 history before implementation.
  ~~~

- [ ] **Step 3: Update Summary section**
  Replace line with Phase 1 description:
  ```
    1. Spec    — <N> items, <elapsed> (parallel + inline retry)
  ```
  With:
  ```
    1. Spec    — <N> items, <elapsed> (parallel agents + inline retry)
  ```

- [ ] **Step 4: Verify Phase 1 restructuring**
  ```bash
  grep -n "parallel agents\|Agent spawn\|concurrency cap\|Single-item\|completed_phase1_items\|keywords_per_item" commands/sprint.md
  ```
  Expected: matches for "Parallel Agents", "Concurrency cap", "Single-item fast path", "completed_phase1_items", "keywords_per_item"

  Also verify sprint.md syntax:
  ```bash
  python3 -c "import yaml; yaml.safe_load(open('commands/sprint.md'))" 2>/dev/null || echo "YAML frontmatter OK (or no frontmatter)"
  head -5 commands/sprint.md
  ```
  Expected: frontmatter intact, no rendering errors

## Task 2: Update ROADMAP mutation and sprint-context patterns

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- ROADMAP is updated once after all agents complete (single batch write), not per-agent
- sprint-context.json stores keywords_per_item (not full context_bundle)
- Sprint resume: .sprint-state tracks completed items per Phase 1 agent
- Error Handling table updated for agent failure mode

**Files:**
- Modify: `commands/sprint.md`

- [ ] **Step 1: Read current sprint.md ROADMAP and sprint-context sections**
  Read `commands/sprint.md` lines around "After Phase 1" and "Write sprint context bundle".

- [ ] **Step 2: Replace sprint-context.json write pattern**
  Find the current sprint-context.json write block (in Phase 1 or the sprint-context section):
  ```python
  sprint_context = {
      "specs": {...},
      "plans": {...},
      "roadmap": roadmap_post_phase1,
      "context_bundle": context_bundle,  # From load-context skill
  }
  ```
  Replace with:
  ```python
  sprint_context = {
      "specs": {...},
      "plans": {...},
      "roadmap": roadmap_post_phase1,
      "keywords_per_item": {...},  # slug → keywords string for downstream load-context calls
  }
  ```
  Remove: `context_bundle` (full ADR content — ~18KB per item, survives /compact unnecessarily)
  Add: `keywords_per_item` dict (slug → keywords string, for downstream load-context calls with cache)

- [ ] **Step 3: Update Error Handling table**
  Replace Phase 1 error handling row:
  ```
  | Phase 1 | Retry exhausted | Halt sprint, surface issue |
  ```
  With:
  ```
  | Phase 1 | Agent fails after retry | Halt sprint, surface issue |
  ```

- [ ] **Step 4: Verify all changes are consistent**
  ```bash
  grep -n "single batch write\|keywords_per_item\|parallel agents\|Agent fails\|completed_phase1_items" commands/sprint.md
  ```
  Expected: at least one match for each term

  Also verify no stale references remain:
  ```bash
  grep -n "context_bundle" commands/sprint.md | grep -v "keywords_per_item"
  ```
  Expected: zero matches (all context_bundle references replaced with keywords_per_item)