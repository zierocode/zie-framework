---
approved: true
approved_at: 2026-04-15
backlog: backlog/optimize-review-loop-token-waste.md
---

# Optimize Review Loop Token Waste — Design Spec

**Problem:** Review confirm passes re-spawn a forked subagent that re-reads all files and re-processes the full context_bundle, wasting ~50-70% of the initial review's tokens per iteration even though only small targeted fixes were applied.
**Appro:** Two optimizations: (1) Replace confirm-pass subagent re-invocation with inline verification — after reviewer pass 1 returns Issues Found, the caller fixes and verifies inline (no new subagent). (2) Reduce context_bundle size by loading only relevant ADRs instead of all 67, and trim project context to what the reviewer actually needs. Keep `context: fork` for pass 1 where isolation is valuable.
**Components:**
- `skills/load-context/SKILL.md` — add ADR relevance filter (root cause — bundles ALL 67 ADRs unconditionally)
- `commands/spec.md` — pass relevance keywords to load-context + inline reviewer verification
- `commands/plan.md` — pass relevance keywords to load-context + inline reviewer verification
- `commands/implement.md` — pass relevance keywords to load-context
- `commands/sprint.md` — pass relevance keywords per item + inline reviewer + filtered sprint-context.json
- `commands/retro.md` — reduce git log injection (50 commits → tag-based only)
- `skills/spec-design/SKILL.md` — reviewer loop (Step 5) + Autonomous mode section
- `skills/brainstorm/SKILL.md` — pass relevance keywords to load-context
- `skills/spec-review/SKILL.md` — scoped Grep/Glob in Phase 3
- `skills/plan-review/SKILL.md` — scoped Grep/Glob in Phase 3
- `skills/impl-review/SKILL.md` — benefits from filtered bundle (no skill-level change needed)

**Data Flow:**

*Current flow (2 passes, subagent per pass):*
1. Caller writes spec/plan
2. Caller invokes reviewer (forked subagent, `context: fork`) → pass 1
3. Reviewer returns Issues Found
4. Caller fixes issues
5. Caller invokes reviewer again (NEW forked subagent) → pass 2 (confirm)
6. Each pass: subagent cold-start → re-load SKILL.md → re-process context_bundle → re-read files → re-do Grep/Glob

*Proposed flow (1 pass + inline verify):*
1. Caller writes spec/plan
2. Caller invokes reviewer (forked subagent, `context: fork`) → pass 1 (unchanged)
3. Reviewer returns Issues Found (structured list)
4. Caller fixes each issue inline
5. Caller verifies each fix inline against the reviewer's issue list (no subagent)
6. All fixes verified → run approve.py → done

**Edge Cases:**
- **Reviewer returns 0 issues on pass 1:** No confirm pass needed — already APPROVED. No change from current flow.
- **Inline verification misses a new issue introduced by the fix:** Accepted risk. Pass 1 already caught structural problems; confirm passes rarely find entirely new categories of issues. The trade-off saves ~50-70% tokens per review cycle.
- **Caller cannot fix an issue:** Surface to user (Interruption Protocol). Same as current behavior on max iterations.
- **Sprint autonomous mode:** Sprint already uses inline reviewers. Update sprint's confirm-pass language from "re-check once → re-run approve.py" to "verify fixes inline → run approve.py".
- **ADR relevance filter too aggressive:** If the filter excludes a relevant ADR, the reviewer may miss a conflict. Mitigated by always including ADR-000-summary (compressed overview of all ADRs) plus any ADRs matching keywords. If no matches, fall back to loading all ADRs (safe default).
- **No keywords available (e.g., /sprint with mixed items):** When keywords can't be extracted, load-context falls back to loading all ADRs — current behavior preserved.
- **impl-review still gets full bundle from /implement:** After load-context supports keywords, /implement passes keywords from the plan. impl-review skill itself needs no change — it receives whatever bundle the caller provides.
- **sprint-context.json without context_bundle:** After /compact, Phase 2/3 can't read full ADR content from the JSON. They call load-context with keywords (cached — fast) instead. The JSON stores only spec/plan content and references.

**Out of Scope:**
- Changing the reviewer skills themselves (`spec-review`, `plan-review`, `impl-review`) — they stay as `context: fork` subagents for pass 1
- Adding `previous_findings` parameter to reviewers — inline verification makes this unnecessary
- Parallel review execution — that's a separate backlog item (`parallel-pipeline-stages`)
- Changing ADR-058 (inline reviewer replaces async impl-review) — this builds on that pattern
- Removing `context: fork` from brainstorm — fork isolation is useful for creative divergence; just reduce ADR payload
- Removing `context: fork` from docs-sync — minor optimization, not worth the risk

## Optimization 2: Context Bundle Reduction

Current state: `load-context` loads ALL 67 ADRs (10KB summary + individual files) and ALL project context (8KB) every time, regardless of feature scope. This bundle is passed to every consumer — 7+ downstream skills/commands receive ~18KB they mostly don't need.

**Framework-wide token waste audit findings:**

| Consumer | Token Waste | What It Reads That It Shouldn't |
|----------|------------|----------------------------------|
| load-context | HIGH (source) | Always bundles ALL ADRs — no subset mechanism |
| /implement | HIGH | Passes full bundle to every impl-review fork per HIGH-risk task |
| /sprint | HIGH | Persists full bundle in sprint-context.json across all phases |
| /plan | MEDIUM | Loads ALL ADRs, passes full bundle to plan-review fork |
| /spec | MEDIUM | Loads ALL ADRs, passes full bundle to spec-review fork |
| brainstorm | MEDIUM | Fork + full ADR content for title-only "skip already-decided" check |
| impl-review | MEDIUM | ALL ADRs via context_bundle for conflict check |
| plan-review | MEDIUM | ALL ADRs via context_bundle for conflict check |
| spec-review | MEDIUM | ALL ADRs via context_bundle for conflict check |
| /retro | LOW | 50-commit git log redundant when tag-based log already loaded |

**Changes:**

### load-context: ADR relevance filter

Add a `keywords` parameter (optional). When provided:
1. Always include ADR-000-summary.md (compressed overview — already exists)
2. Match keywords against ADR filenames/titles
3. Include only matching ADRs + ADR-000-summary in the bundle
4. If no keywords provided → fall back to loading all ADRs (safe default, current behavior)
5. If keywords provided but no matches → fall back to loading all ADRs

### All load-context callers: pass relevance keywords

Each caller extracts keywords from its context and passes them to load-context:
- `/spec` → keywords from backlog item (Problem + Approach sections)
- `/plan` → keywords from spec (Problem + Approach sections)
- `/implement` → keywords from plan (Goal + Architecture sections)
- `/sprint` → keywords per item from backlog items
- `brainstorm` → keywords from brainstorm topic

### Reviewer: Scoped Grep/Glob

Current: Phase 3 file existence checks use broad Grep/Glob across the entire codebase.
Change: Scope Grep/Glob to only the paths listed in the spec/plan Components section. If the spec lists `skills/spec-design/SKILL.md`, only grep within `skills/` and `commands/`, not `tests/`, `hooks/`, or `zie-framework/archive/`.

### /retro: reduce git log injection

Current: Both `git log` (since last tag) and `git log -50` are injected. Redundant.
Change: Remove `git log -50` — tag-based log is sufficient for retro context.

### /sprint: filtered sprint-context.json

Current: `sprint-context.json` persists full `context_bundle` (all ADRs) across phases.
Change: Only persist `context_bundle` metadata (not the full ADR content). Downstream phases that need ADRs call load-context with keywords (which uses cache — fast).