---
approved: true
approved_at: 2026-04-11
backlog:
---

# Context Efficiency — Design Spec

**Problem:** Framework over-spends tokens in three areas: (A) reviewer skills load full content (~1,800 tokens each) every invocation even when only a summary is needed; (B) `subagent-context.py` injects the same project-state context redundantly within a single session on consecutive SubagentStart events; (C) subagents receive full project context bundles when each agent type only needs a small subset.

**Approach:** Three targeted fixes — (A) progressive skill loading: FAST PATH block (≤120 tokens) at the top of long skills; (B) session-scoped context cache keyed on session_id: subagent-context.py skips inject on cache hit; (C) per-agent context budget table in subagent-context.py.

**Token Baseline (Fix A justification):**
- `spec-reviewer/SKILL.md`: ~1,800 tokens currently; FAST PATH target: ≤120 tokens (~93% reduction on simple cases)
- `plan-reviewer/SKILL.md`: ~1,600 tokens; same target
- `impl-reviewer/SKILL.md`: ~900 tokens; FAST PATH target: ≤80 tokens
- `load-context/SKILL.md`: ~400 tokens; FAST PATH target: ≤60 tokens
Threshold for applying FAST PATH: skill content > 300 tokens. All 4 files qualify.

**Out of Scope:** Context dedup for hooks other than subagent-context.py (only subagent-context.py injects project state today). FAST PATH for skills under 300 tokens.

**Components:**
- `skills/spec-reviewer/SKILL.md` — add FAST PATH header
- `skills/plan-reviewer/SKILL.md` — add FAST PATH header
- `skills/impl-reviewer/SKILL.md` — add FAST PATH header
- `skills/load-context/SKILL.md` — add FAST PATH header
- `hooks/subagent-context.py` — extend with (B) session cache check + (C) per-agent budget table
- `hooks/session-cleanup.py` — extend cleanup list to include session context cache file

**Session Cache File:**
- Path: `project_tmp_path("session-context", project)` (using existing `utils_io.project_tmp_path()`)
- Format: flag file (existence check only — no content read/validation needed)
- Write: `utils_io.atomic_write()` (write-to-temp-then-rename, consistent with codebase pattern)
- Cleanup: `session-cleanup.py` calls `unlink(missing_ok=True)` on this path — handles missing file gracefully

**Data Flow:**

*A — Progressive Skill Loading:*
1. Each qualifying skill gets a `<!-- FAST PATH -->` block at the top (≤120 tokens): one-line purpose, one-line when-to-use, 3-5 quick steps
2. Claude reads FAST PATH first; if task is straightforward → proceed without reading DETAIL section
3. Full skill content follows under `<!-- DETAIL: load only if fast path insufficient -->` marker
4. No behavioral change — purely reading-order optimization; existing tests must pass unchanged

*B — Hook Context Dedup (subagent-context.py only):*
1. On SubagentStart event: check for session cache flag at `project_tmp_path("session-context", project)`
2. Cache hit (flag exists, same session): skip project-state injection entirely → exit 0
3. Cache miss: inject project state as normal → write cache flag via `atomic_write()`
4. session_id missing from event: fallback to always-inject (safe, just less efficient)
5. `session-cleanup.py` deletes cache flag on session end via `unlink(missing_ok=True)`

*C — Subagent Context Budget (subagent-context.py):*

**ADR-046 supersession:** ADR-046 restricted `subagent-context.py` to Explore and Plan agents via an early-exit guard (`if not re.search(r'Explore|Plan', agent_type): sys.exit(0)`). This spec supersedes that guard — the Explore/Plan restriction is replaced by the per-agent budget table below. The budget table handles all agent types explicitly, with a conservative default for unknowns.

`agent_type` field comes from SubagentStart event (already available in `subagent-context.py`).

| agent_type | receives | excluded |
|---|---|---|
| spec-reviewer | spec file + ADR-000-summary.md | project state, git log, roadmap |
| plan-reviewer | plan file + spec file + ADR-000-summary.md | backlog, roadmap, git log |
| impl-reviewer | changed files + plan file | ADR, full project state |
| resync | git log + file structure | specs, plans, decisions, backlog |
| brainstorm | no injection (skill has own Phase 1 discovery) | all |
| (unknown) | ADR-000-summary.md + project state summary | git log, full spec/plan set |

**Error Handling:**
- Cache flag unwriteable: log warning to stderr, continue without caching (inject runs normally — never block)
- session_id missing from event: fallback to always-inject
- FAST PATH block missing from a skill: no regression — skill works as before, loads full content
- Unknown agent_type: send conservative default bundle (last row in table above)
- session-cleanup unlink fails: log warning, exit 0 (stale flag causes one redundant skip next session — acceptable)

**Testing (`tests/unit/test_context_efficiency.py`):**
- Unit: FAST PATH block present and ≤120 tokens in each of the 4 modified skills
- Unit: subagent-context skips inject on cache hit, injects + writes flag on cache miss
- Unit: session-cleanup unlinks cache flag; missing file handled gracefully (no exception)
- Unit: subagent-context sends correct bundle per agent_type
- Unit: unknown agent_type falls back to conservative default
- Unit: cache write failure exits 0, does not block (error path, @pytest.mark.error_path)
- Regression: all existing spec-reviewer, plan-reviewer, impl-reviewer behavior tests pass unchanged
