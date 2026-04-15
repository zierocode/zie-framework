---
approved: true
approved_at: 2026-04-15
backlog: backlog/optimize-review-loop-token-waste.md
---

# Optimize Review Loop Token Waste — Implementation Plan

**Goal:** Eliminate confirm-pass subagent re-invocation and reduce context_bundle waste, saving ~50-70% tokens per review cycle.
**Architecture:** Two optimizations: (1) Replace confirm-pass subagent re-invocation with inline verification. (2) Reduce context_bundle size — ADR relevance filter in load-context, scoped Grep/Glob in reviewers, keyword passthrough from callers, git log reduction in retro.
**Tech Stack:** Markdown (commands/skills), Python (load-context cache logic in hooks/utils_cache.py)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/load-context/SKILL.md` | Add `keywords` parameter for ADR relevance filter |
| Modify | `hooks/utils_cache.py` | Add keyword-based ADR filtering to `read_adrs_unified()` |
| Modify | `commands/spec.md` | Pass keywords to load-context + inline reviewer verification |
| Modify | `commands/plan.md` | Pass keywords to load-context + inline reviewer verification |
| Modify | `commands/implement.md` | Pass keywords to load-context |
| Modify | `commands/sprint.md` | Pass keywords per item + inline reviewer + filtered sprint-context.json |
| Modify | `commands/retro.md` | Remove `git log -50` injection |
| Modify | `skills/spec-design/SKILL.md` | Replace reviewer loop with inline verification |
| Modify | `skills/brainstorm/SKILL.md` | Pass keywords to load-context |
| Modify | `skills/spec-reviewer/SKILL.md` | Scoped Grep/Glob in Phase 3 |
| Modify | `skills/plan-reviewer/SKILL.md` | Scoped Grep/Glob in Phase 3 |

---

## Task 1: Add ADR relevance filter to load-context

**Acceptance Criteria:**
- load-context accepts optional `keywords` parameter
- When keywords provided: loads only ADR-000-summary + matching ADRs
- When keywords provided but no matches: falls back to loading all ADRs
- When no keywords: loads all ADRs (current behavior, safe default)
- utils_cache.py `read_adrs_unified()` supports keyword filtering
- Existing tests pass

**Files:**
- Modify: `skills/load-context/SKILL.md`
- Modify: `hooks/utils_cache.py`

- [ ] **Step 1: Read current load-context SKILL.md and utils_cache.py**
  Read both files to get exact text of ADR loading logic.

- [ ] **Step 2: Write failing test (RED)**
  Create test for `read_adrs_unified(keywords=...)`:
  ```python
  # tests/unit/test_utils_cache.py — add to existing file or create new
  def test_read_adrs_unified_with_keywords_filters():
      """ADR relevance filter: only returns summary + matching ADRs."""
      result = read_adrs_unified(cwd, keywords=["sprint", "resilience"])
      # Must always include ADR-000-summary
      assert "ADR-000" in result or "summary" in result.lower()
      # Must NOT include unrelated ADRs (e.g., ADR-001 if not about sprint/resilience)
      # Exact assertion depends on ADR content — check at least one non-matching ADR is excluded

  def test_read_adrs_unified_with_keywords_no_match_fallback():
      """If keywords match nothing, fall back to all ADRs."""
      result_all = read_adrs_unified(cwd)
      result_no_match = read_adrs_unified(cwd, keywords=["xyzzy_nonexistent"])
      assert result_no_match == result_all  # safe fallback
  ```
  Run: `make test-unit` — must FAIL (function doesn't accept `keywords` yet)

- [ ] **Step 3: Implement keyword filtering (GREEN)**
  Update `read_adrs_unified()` in `hooks/utils_cache.py`. Add `keywords=None` parameter:
  1. If `keywords` is None or empty → return all ADRs (current behavior)
  2. Always load ADR-000-summary.md
  3. Match keywords (case-insensitive) against ADR filenames and first-line titles
  4. Return summary + matching ADRs only
  5. If no matches → return all ADRs (safe fallback)

  Run: `make test-unit` — must PASS

- [ ] **Step 4: Update load-context SKILL.md**
  Add `keywords` parameter to argument-hint and steps. Step 0 checks for keywords; if present, passes to `read_adrs_unified(keywords=...)`.
  Replace Step 0 fast-path:
  ```
  **Step 0: Load ADRs via cache**
  - If `keywords` argument provided → `adrs_content = cache.get_or_compute("adrs:{keywords_hash}", session_id, compute_fn, ttl=3600)` where compute_fn calls `read_adrs_unified(cwd, keywords=keywords)`
  - If no keywords → current behavior: `adrs_content = cache.get_or_compute("adrs", session_id, compute_fn, ttl=3600)`
  ```

  Run: `make test-unit` — must PASS

## Task 2: Update all load-context callers to pass keywords

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- /spec extracts keywords from backlog item → passes to load-context
- /plan extracts keywords from spec → passes to load-context
- /implement extracts keywords from plan → passes to load-context
- /sprint extracts keywords per item → passes to load-context
- brainstorm extracts keywords from topic → passes to load-context

**Files:**
- Modify: `commands/spec.md`
- Modify: `commands/plan.md`
- Modify: `commands/implement.md`
- Modify: `commands/sprint.md`
- Modify: `skills/brainstorm/SKILL.md`

- [ ] **Step 1: Read all 5 caller files**
  Read current load-context invocation in each file.

- [ ] **Step 2: Update each caller**
  For each caller, add keyword extraction before load-context call. Insert after reading the source content:

  **/spec** (`commands/spec.md`):
  Replace:
  ```
  Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
  ```
  With:
  ```
  Extract keywords from backlog item (Problem + Approach sections — split on whitespace, remove stop words, take top 6 unique terms)
  Invoke `Skill(zie-framework:load-context, keywords='<extracted>')` → result available as `context_bundle`
  ```

  **/plan** (`commands/plan.md`):
  Replace:
  ```
  Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
  ```
  With:
  ```
  Extract keywords from spec (Problem + Approach sections — split on whitespace, remove stop words, take top 6 unique terms)
  Invoke `Skill(zie-framework:load-context, keywords='<extracted>')` → result available as `context_bundle`
  ```

  **/implement** (`commands/implement.md`):
  Replace:
  ```
  Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
  ```
  With:
  ```
  Extract keywords from plan (Goal + Architecture sections — split on whitespace, remove stop words, take top 6 unique terms)
  Invoke `Skill(zie-framework:load-context, keywords='<extracted>')` → result available as `context_bundle`
  ```

  **/sprint** (`commands/sprint.md`):
  Replace:
  ```
  Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
  ```
  With:
  ```
  Extract keywords per item from backlog items (Problem + Approach — top 6 terms each)
  Invoke `Skill(zie-framework:load-context, keywords='<first-item-keywords>')` → result available as `context_bundle`
  ```

  **brainstorm** (`skills/brainstorm/SKILL.md`):
  Replace:
  ```
  Invoke `Skill(zie-framework:load-context)` -> result available as `context_bundle`
  ```
  With:
  ```
  Extract keywords from brainstorm topic (split on whitespace, remove stop words, take top 6 unique terms)
  Invoke `Skill(zie-framework:load-context, keywords='<extracted>')` -> result available as `context_bundle`
  ```

  Run: `make test-unit` — not applicable (Markdown-only changes for commands/skills)

- [ ] **Step 3: Verify keywords flow**
  Grep for `load-context` invocations to confirm all pass keywords:
  ```bash
  grep -n "load-context" commands/spec.md commands/plan.md commands/implement.md commands/sprint.md skills/brainstorm/SKILL.md
  ```
  Expected: each invocation includes keywords parameter

## Task 3: Add scoped Grep/Glob to reviewers

<!-- depends_on: none -->

**Acceptance Criteria:**
- spec-reviewer Phase 3 scopes Grep/Glob to paths in spec's Components section
- plan-reviewer Phase 3 scopes Grep/Glob to paths in plan's File Map
- Both reviewers still fall back to broad scope if no paths found in spec/plan

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`

- [ ] **Step 1: Read both reviewer SKILL.md files**
  Read Phase 3 sections for exact text.

- [ ] **Step 2: Update spec-reviewer Phase 3**
  Add scoped path extraction before file existence checks. Replace Phase 3 intro:
  ```
  1. **File existence** — named component files that don't exist and aren't marked "Create".
  ```
  With:
  ```
  1. **File existence** — extract directory paths from spec's Components section. Scope Glob/Grep to those directories only. If no paths found → use current broad scope. Named component files that don't exist and aren't marked "Create" are flagged.
  ```

  Run: `make test-unit` — not applicable (Markdown-only change)

- [ ] **Step 3: Update plan-reviewer Phase 3**
  Replace Phase 3 step 1:
  ```
  1. **File existence** — list file-map files that don't exist and aren't marked "Create".
  ```
  With:
  ```
  1. **File existence** — extract directory paths from plan's File Map. Scope Glob/Grep to those directories only. If no paths found → use current broad scope. List file-map files that don't exist and aren't marked "Create".
  ```

  Run: `make test-unit` — not applicable (Markdown-only change)

## Task 4: Update reviewer loop to inline verification

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- spec-design Step 5 no longer mentions re-invoking reviewer after fixes
- spec-design Autonomous mode: "fix inline → verify inline → run approve.py"
- plan.md plan-reviewer gate: invoke once → fix → verify inline → approve
- spec.md reviewer invocation: no "re-invoke" or "confirm pass"
- sprint.md Phase 1 reviewer: inline verification language
- No "re-check once", "re-invoke", "confirm pass", "pass 2", "Max N iterations" in any modified file

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Modify: `commands/plan.md`
- Modify: `commands/spec.md`
- Modify: `commands/sprint.md`

- [ ] **Step 1: Read all 4 files**
  Read current reviewer loop/gate sections in each file.

- [ ] **Step 2: Update spec-design SKILL.md**
  Step 5:
  ```
  5. **Spec reviewer loop** — invoke `Skill(zie-framework:spec-reviewer)` once:
     - ✅ APPROVED → proceed to Step 6
     - ❌ Issues Found → fix all issues inline → verify each fix against the issue list
       (no re-invocation of reviewer — inline verification replaces confirm pass)
     - If any issue cannot be fixed → surface to user
  ```
  Autonomous mode:
  - Replace: `fix inline (1 pass) → re-check once → re-run approve.py on pass`
  - With: `fix all issues inline → verify each fix against issue list → run approve.py`
  - Replace: `Second failure → surface to user`
  - With: `Any issue unfixable → surface to user`

- [ ] **Step 3: Update plan.md plan-reviewer gate**
  Replace confirm pass language:
  ```
  3. If ❌ Issues Found → fix ALL issues listed → verify each fix inline against issue list
     (no re-invocation of reviewer — inline verification replaces confirm pass)
     - If all fixes verified → proceed to Zie approval below
     - If any issue unfixable → surface to Zie
  ```

- [ ] **Step 4: Update spec.md reviewer invocation**
  Replace: `If ❌ Issues Found → fix → re-invoke → repeat until ✅ APPROVED. Max 3 iterations`
  With: `If ❌ Issues Found → fix all issues → verify each fix inline against issue list → run approve.py`
  Remove: `Max 3 iterations → surface to human`

- [ ] **Step 5: Update sprint.md Phase 1 reviewer section**
  Replace: `❌ Issues Found → fix inline (1 pass), re-check once → re-run approve.py on pass`
  With: `❌ Issues Found → fix all issues inline → verify each fix against issue list → run approve.py`
  Replace: `Second failure → interrupt (Interruption Protocol case 2)`
  With: `Any issue unfixable → interrupt (Interruption Protocol case 2)`

- [ ] **Step 6: Consistency check**
  ```bash
  grep -rn "re-invoke\|confirm pass\|pass 2\|re-check once\|Max [23] iter" skills/spec-design/SKILL.md commands/plan.md commands/spec.md commands/sprint.md
  ```
  Expected: zero matches

  Run: `make test-unit` — not applicable (Markdown-only changes)

## Task 5: Reduce /retro git log + filter sprint-context.json

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- /retro no longer injects `git log -50` (tag-based log is sufficient)
- sprint-context.json stores spec/plan content + references, not full context_bundle
- Sprint Phase 2/3 call load-context with keywords (cached) instead of reading from JSON

**Files:**
- Modify: `commands/retro.md`
- Modify: `commands/sprint.md`

- [ ] **Step 1: Read current retro.md and sprint.md**
  Get exact text of git log injection and sprint-context.json sections.

- [ ] **Step 2: Remove `git log -50` from retro.md**
  Find the line that injects `git log -50` (or similar 50-commit injection). Remove it. Keep only the tag-based `git log` injection. Exact replacement depends on current text — read file first.

  Run: `make test-unit` — not applicable (Markdown-only change)

- [ ] **Step 3: Update sprint-context.json in sprint.md**
  Find the sprint-context.json write block. Replace:
  ```python
  sprint_context = {
      "specs": {...},
      "plans": {...},
      "roadmap": roadmap_post_phase1,
      "context_bundle": context_bundle,  # From load-context skill
  }
  ```
  With:
  ```python
  sprint_context = {
      "specs": {...},
      "plans": {...},
      "roadmap": roadmap_post_phase1,
      "keywords_per_item": {...},  # Keywords per item for downstream load-context calls
  }
  ```
  Remove: `context_bundle` (full ADR content — ~18KB per item, survives /compact unnecessarily)
  Add: `keywords_per_item` dict (slug → keywords string, for downstream load-context calls with cache)

  Phase 2/3: instead of reading context_bundle from JSON, call `Skill(zie-framework:load-context, keywords=sprint_context["keywords_per_item"][slug])` (cached — fast).

  Run: `make test-unit` — not applicable (Markdown-only change)

- [ ] **Step 4: Final verification**
  ```bash
  make test-unit
  ```
  Must PASS — no Python code changes in this task, but verify no regressions