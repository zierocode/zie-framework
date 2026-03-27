---
approved: true
approved_at: 2026-03-27
backlog: batch — medium-effort-optimization, token-efficiency-sprint, parallelize-framework-ops, artifact-archive-strategy, implement-no-plan-guard, architecture-cleanup, standards-compliance
---

# Sprint 3: Framework Optimization — Design Spec

**Problem:** zie-framework v1.10.2 has 7 optimization items: effort mismatches with Sonnet 4.6 medium, token waste in prompts, serial operations that can parallelize, artifact bloat, missing SDLC guard, architectural inconsistencies, and compliance gaps.

**Approach:** Three parallel tracks. Track A (effort + tokens), Track B (parallelism + archive + guard), Track C (architecture + standards). Release as v1.11.0.

**Components:**

Track A — Effort + Token Efficiency:
- `skills/*/SKILL.md` — update `effort:` frontmatter to `medium` (all except spec-design/zie-audit which justify `high`)
- `commands/*.md` — audit effort fields; trim verbose intros in zie-implement, zie-release, zie-retro
- `hooks/intent-sdlc.py` — compile regex patterns at module level (not per-call)
- `zie-framework/decisions/ADR-020-effort-routing.md` — document effort strategy

Track B — Parallelism + Archive + Guard:
- `commands/zie-retro.md` — launch ADR write + ROADMAP update in parallel Agent calls; brain store after both complete
- `zie-framework/archive/` — create directory structure; add `make archive` target to Makefile
- `commands/zie-release.md` — add archive step post-merge
- `commands/zie-implement.md` — add pre-flight: block if no approved plan in Ready lane
- `hooks/utils.py` — add `parse_roadmap_ready()` helper

Track C — Architecture + Standards:
- `hooks/task-completed-gate.py` — read `TEST_INDICATORS` from `.config` with fallback
- `hooks/session-resume.py` — fix log prefix from `[zie]` to `[zie-framework]`
- `tests/unit/test_versioning_gate.py` — add VERSION == plugin.json version assertion
- `CLAUDE.md` — document integration test exclusion; add `make sync-version` to release checklist
- `.github/workflows/ci.yml` — change `make test` → `make test-unit` (integration tests require live Claude session; unsuitable for CI)

**Data Flow:**

**A1 — Effort frontmatter audit**
- Grep all `effort:` fields in `skills/*/SKILL.md` and `commands/*.md`
- Update to `medium` where currently `high` without justification
- Keep `high` for: `spec-design` (full dialogue), `zie-implement` (full TDD loop)
- `skills/zie-audit/SKILL.md` is an active skill invoked by `/zie-audit` — it is NOT being deleted. Skip this file for effort audit (it's already `medium`).
- Write ADR-020 documenting the routing rationale

**A2 — Token trim (zie-implement, zie-release, zie-retro)**
- Remove redundant intro sentences that repeat the frontmatter `description:` field
- Target: each command intro ≤3 sentences before the step list
- Do NOT remove any actual workflow steps or acceptance criteria

**A3 — Intent regex caching (intent-sdlc.py)**
- Current: regex compiled in function body on every hook call
- Fix: move `PATTERNS = {stage: re.compile(r'...') for ...}` to module level
- Result: compiled once per process, not per invocation

**B1 — Parallelize retro (zie-retro.md)**
- Current: ADR write → ROADMAP update → brain store (serial)
- Fix: launch ADR write and ROADMAP update as parallel Agent calls (both `run_in_background: false`); await both before brain store
- Constraint: ADR file and ROADMAP file are different — no write conflict
- Timeout: each Agent call uses the standard 120s window per ADR-014; both launched simultaneously so total wall time ≈ max(ADR time, ROADMAP time)
- Failure mode: if either Agent call fails (exception or timeout) → brain store is skipped entirely. Both timeout and exception are treated identically — skip, do not retry.

**B2 — Archive strategy (Makefile + zie-release.md)**
- Create `zie-framework/archive/backlog/`, `archive/specs/`, `archive/plans/`
- `make archive` target: move completed backlog items (referenced in Done lane) + their linked specs/plans to archive/
- `zie-release.md`: add archive step after merge — `make archive` to move shipped artifacts
- Archive dirs excluded from reviewer context bundles (they read from active dirs only)
- Slug matching: match backlog items in Done lane to archive by slug, not exact filename

**B3 — /zie-implement guard (zie-implement.md + utils.py)**
- Add `parse_roadmap_ready(path: Path) -> list[str]` to `utils.py`: `return parse_roadmap_section(path, "Ready")` — reuse existing `parse_roadmap_section()` helper, same pattern as `parse_roadmap_now()`
- In `/zie-implement` startup: read Ready lane; if empty → print error + stop
- If Now lane has active item → print WIP error + stop
- Guard is a markdown pre-flight check block (shell command in command file)
- If ROADMAP.md missing entirely → print clear error: "ROADMAP.md not found — run /zie-init" not crash

**C1 — Architecture fixes (utils.py + task-completed-gate.py)**
- `parse_roadmap_now()` `warn_on_empty` parameter: verify it's already called where needed
- `task-completed-gate.py`: read `TEST_INDICATORS` from `load_config(cwd).get("test_indicators", DEFAULT_INDICATORS)`; empty list in config → use DEFAULT_INDICATORS (never leave gate with no indicators)
- `session-resume.py:26`: change `[zie] warning:` → `[zie-framework] session-resume:`

**C2 — Standards (tests + CI + docs)**
- `tests/unit/test_versioning_gate.py`: add `assert VERSION == plugin_json["version"]`
- `.github/workflows/ci.yml`: change `make test` → `make test-unit`; justification: `make test` includes `make test-int` which requires a live Claude session — unsuitable for CI. `make test-unit` runs all 1500+ unit tests without external dependencies.
- `CLAUDE.md`: add "Integration tests require live Claude session — run `make test-int` separately" under Development Commands

**Parallelize-framework-ops scope clarification:**
- The `parallelize-framework-ops` backlog item covers: (1) audit parallelization — zie-audit already parallelizes its 9 dimensions into 3 agent batches per its SKILL.md; no changes needed; (2) retro phase parallelization — addressed in B1; (3) test gate parallelization — deferred (complex refactor, out of scope). B1 fulfills the retro portion; audit already parallelized; test gates deferred.

**Acceptance Criteria:**

1. **Effort** — `grep -r "effort: high" skills/` returns only spec-design and zie-implement; all others `medium`
2. **Token trim** — word count of zie-implement.md, zie-release.md, zie-retro.md each reduced by ≥10%
3. **Regex cache** — `grep "re.compile" hooks/intent-sdlc.py` shows patterns at module level, not in function
4. **Archive** — `zie-framework/archive/backlog/`, `archive/specs/`, `archive/plans/` directories exist; `make archive` moves Done items
5. **Implement guard** — running `/zie-implement` with empty Ready lane prints error and stops; unit test passes
6. **parse_roadmap_ready()** — in utils.py; returns list of items from Ready lane
7. **Retro parallel** — zie-retro.md uses parallel Agent calls for ADR + ROADMAP; documented
8. **Version gate** — test_versioning_gate.py passes; fails if VERSION ≠ plugin.json
9. **Log prefix** — `grep "\[zie\]" hooks/` returns no matches
10. **CI** — `.github/workflows/ci.yml` runs `make test-unit` (not `make test`)
11. **TEST_INDICATORS** — configurable via `.config`; default behavior unchanged
12. **All existing tests pass** — `make test-unit` green

**Edge Cases:**
- Archive: backlog items in Done lane may reference specs/plans with different dates — match by slug, not exact filename
- Implement guard: If ROADMAP.md missing entirely → print clear error ("ROADMAP.md not found — run /zie-init") not crash
- Retro parallel: if ADR write fails, ROADMAP update still completes (independent); brain store skipped on failure
- TEST_INDICATORS from config: empty list in config → use DEFAULT_INDICATORS (never leave gate with no indicators)
- CI workflow: already configured to run on push/PR to main and dev branches — preserve existing branch filter

**Dependencies:**
- Sprint 3 is independent of Sprint 2 with one exception: `skills/zie-audit/SKILL.md` deletion (Sprint 2 dead-code-cleanup). Sprint 3 A1 handles this conditionally. All other Sprint 3 items are unblocked.
- The 4 HIGH items in ROADMAP (symlink guards, sdlc-permissions, exec_module tests, docs sync) are addressed in Sprint 2 — Sprint 3 is MEDIUM priority and can proceed in parallel or after.

**Out of Scope:**
- Git status caching (too invasive for this sprint; requires TTL + file lock)
- Full async hook conversion (requires hooks.json changes + testing each hook)
- MCP bundle publication (separate future sprint)
- Replacing all `get_cwd().name` calls (large refactor; follow-on to consolidate-utils)
- Test gate parallelization (complex; follow-on sprint)
