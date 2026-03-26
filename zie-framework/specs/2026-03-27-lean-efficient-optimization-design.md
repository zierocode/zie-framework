---
approved: true
approved_at: 2026-03-27
backlog: backlog/lean-efficient-optimization.md
---

# Lean & Efficient Optimization — Design Spec

**Problem:** zie-framework consumes ~70% of every Claude Code session's token budget on framework overhead rather than user work — a typical session incurs ~12,110 tokens of hook/context overhead vs ~5,000 tokens of actual work, and a single zie-audit run costs 50K–200K tokens (Opus × 5 agents × 25 WebSearch queries).

**Approach:** Full-stack optimization across 5 layers — hook consolidation, audit agent right-sizing, effort level correction, command slimming (+ uncap parallel agents), and plans archive. Implemented in priority order: Layers 1–3 deliver ~85% of savings at low risk; Layers 4–5 are isolated cleanup. Parallel agent caps removed entirely since token cost is identical to sequential — only `depends_on` and file-conflict detection should govern serialization.

**ADR Changes:** Supersedes ADR-012 (zie-audit Opus reservation) via ADR-021. ADR-017 (impl-reviewer sonnet/medium) is explicitly preserved — impl-reviewer downgrade is out of scope.

**Components:**
- `hooks/intent-detect.py` + `hooks/sdlc-context.py` → merged into `hooks/intent-sdlc.py`
- `hooks/utils.py` — add `get_cached_roadmap(session_id, ttl=30)`
- `hooks/hooks.json` — remove intent-detect+sdlc-context entries, add intent-sdlc; set wip-checkpoint background:true; set safety_check_mode default to regex
- `commands/zie-audit.md` — 5 Opus agents → 3 Sonnet + synthesis, effort:high→medium, WebSearch 25→15
- `skills/zie-audit/SKILL.md` — model:opus→sonnet, effort:high→medium
- `commands/zie-plan.md` — effort:high→medium, remove parallel cap
- `commands/zie-retro.md` — effort:high→medium
- `commands/zie-implement.md` — remove parallel cap, trim to ~150 lines
- `Makefile` — add `archive-plans` target
- `hooks/knowledge-hash.py` — skip `plans/archive/`
- `commands/zie-resync.md` — exclude `plans/archive/` from resync scope
- `zie-framework/decisions/ADR-021-lean-audit-sonnet-synthesis.md` — new ADR superseding ADR-012

---

## Layer 1 — Hook Consolidation

### Merge UserPromptSubmit hooks

Combine `intent-detect.py` + `sdlc-context.py` into single `intent-sdlc.py`:
- Read ROADMAP.md once → build intent context + SDLC context in same pass
- Return single `additionalContext` payload
- Delete both source files; update hooks.json

### ROADMAP.md session cache

Add `get_cached_roadmap(session_id, ttl=30)` to `hooks/utils.py`:

```python
def get_cached_roadmap(session_id: str, ttl: int = 30) -> str | None:
    cache_path = Path(f"/tmp/zie-{session_id}/roadmap.cache")
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < ttl:
            return cache_path.read_text()
    return None

def write_roadmap_cache(session_id: str, content: str) -> None:
    cache_dir = Path(f"/tmp/zie-{session_id}")
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "roadmap.cache").write_text(content)
```

All hooks that read ROADMAP.md call `get_cached_roadmap()` first; fall back to disk read + `write_roadmap_cache()`.

Affected hooks: `intent-sdlc.py`, `subagent-context.py`, `sdlc-compact.py`, `failure-context.py`

*Note: The function signatures above are design specifications. Actual implementation belongs in the plan/implement phase — see `hooks/utils.py` as the target module.*

### safety_check_agent default → regex

In hooks.json default config: `safety_check_mode: "regex"` (was `"agent"`).
Opt-in per project via `.config`: `"safety_check_mode": "agent"` for projects that need AI-powered safety eval.

### wip-checkpoint → async

In hooks.json: add `"background": true` to wip-checkpoint PostToolUse entry.
No blocking wait; Claude continues immediately after Edit/Write.

---

## Layer 2 — zie-audit Overhaul

### 5 Opus agents → 3 Sonnet agents + 1 synthesis

Consolidate audit dimensions:

| Before | After |
|--------|-------|
| Agent A: Security | Agent 1: Security (unchanged) |
| Agent B: Lean/Efficiency | Agent 2: Code Health (Lean + Quality + Testing) |
| Agent C: Quality/Testing | ↑ merged |
| Agent D: Documentation | Agent 3: Structural (Docs + Architecture + Patterns) |
| Agent E: Architecture | ↑ merged |
| — | Agent 4: Synthesis (Sonnet) — deduplicates, scores, ranks all findings |

### Model + effort change

- All 4 agents: `model: sonnet`, `effort: medium`
- Previously: `model: opus`, `effort: high`
- **Supersedes ADR-012** (Opus reserved for zie-audit): ADR-012 justified Opus on the basis of 9-dimension synthesis + 15+ WebSearch + parallel cross-referencing. This spec changes the architecture — the synthesis pass now handles cross-referencing explicitly, and Sonnet 4.6 capability for pattern-match auditing is substantially higher than when ADR-012 was written. ADR-021 records this reversal.
- Also update `test_model_effort_frontmatter.py` EXPECTED map: move zie-audit from opus to sonnet tier

### WebSearch cap 25 → 15

Each agent allocated max 5 targeted queries (was broadcast sweep).
Synthesis agent: 0 WebSearch (works from agent outputs only).

### Expected cost reduction

```
Before: 5 × Opus × ~40K tokens + 25 WebSearch  ≈ 200K tokens
After:  3 × Sonnet × ~15K + 1 × Sonnet × ~10K  ≈  55K tokens  (↓72%)
```

---

## Layer 3 — Effort Right-sizing

| File | Before | After | Rationale |
|------|--------|-------|-----------|
| `commands/zie-plan.md` | effort: high | effort: medium | Structured output task; not open-ended reasoning |
| `commands/zie-retro.md` | effort: high | effort: medium | Summarize + format; pattern recognition not deep inference |

**Principle:** `effort: high` reserved for open-ended design (zie-spec) and unstructured debugging (zie-fix). Structured output tasks default to medium.

**Explicitly preserved (ADR-017):** `impl-reviewer` remains `model: sonnet, effort: medium`. ADR-017 established that code review requires reasoning to detect subtle logic errors and spec violations — not checklist enumeration. Fork isolation already bounds the cost to the changed-files bundle only.

---

## Layer 4 — Command Slimming + Remove Parallel Cap

### Remove parallel agent caps

Current caps (zie-implement: 4, zie-plan: 4) are arbitrary. Token cost of parallel vs sequential execution is identical — the same work happens either way, parallel just finishes faster. Reducing the cap (backlog originally suggested max 3/max 2) saves zero tokens while adding latency. Full removal is therefore strictly better: max speed at the same credit cost, with `depends_on` and file-conflict detection remaining as the only valid serialization constraints.

- `commands/zie-implement.md`: remove `max parallel tasks: 4` constraint; keep `depends_on` conflict logic
- `commands/zie-plan.md`: remove `max 4 parallel Agents` constraint

### Slim zie-implement.md 351 → ~150 lines

Extract verbose sections into terse inline comments:
- Parallelization explanation: replace 30-line description with 3-line comment + `depends_on` example
- Dependency analysis walkthrough: collapse to bullet list
- File conflict detection prose: replace with single-line rule

### Slim zie-audit.md 330 → ~150 lines

Already redesigned in Layer 2. Dimension descriptions → terse bullets (2 lines per dimension max).

---

## Layer 5 — Archive plans/

Current size: 1.6 MB of historical implementation plans.

### Makefile target

```makefile
archive-plans:
	@mkdir -p zie-framework/plans/archive
	@find zie-framework/plans -maxdepth 1 -name "*.md" \
	  -mtime +60 -exec mv {} zie-framework/plans/archive/ \;
	@echo "[zie-framework] Archived plans older than 60 days"
```

- Manual only — run via `make archive-plans`
- Added to `/zie-release` post-ship checklist (not automated)

### Exclude archive from tooling

- `knowledge-hash.py`: skip `zie-framework/plans/archive/` in hash computation
- `commands/zie-resync.md`: exclude `plans/archive/` from resync scope

---

## Data Flow

**Before (15-message session, 8 edits):**
```
UserPromptSubmit × 15  →  2 hooks × 550t each        =  8,250t
PreToolUse × 8         →  safety_check_agent + sani   =  3,200t
PostToolUse × 8        →  wip-checkpoint sync          =    640t
ROADMAP reads × 6-8    →  no cache
Total overhead:                                         ~12,110t
```

**After:**
```
UserPromptSubmit × 15  →  1 hook × 350t (cached ROADMAP) =  5,250t
PreToolUse × 8         →  sanitizer only (regex safety)   =  1,200t
PostToolUse × 8        →  wip-checkpoint async            =      0t
ROADMAP reads × 1      →  cached after first read
Total overhead:                                            ~6,450t  (↓47%)
```

**zie-audit:**
```
Before:  ~200K tokens (5 Opus + 25 WebSearch)
After:   ~55K tokens  (3 Sonnet + synthesis + 15 WebSearch)  (↓72%)
```

---

## Edge Cases

| Case | Mitigation |
|------|-----------|
| ROADMAP cache stale mid-session (user edits ROADMAP manually) | TTL 30s is the only invalidation mechanism — no hook writes ROADMAP.md directly (only commands do, outside hook scope). At worst, a stale read lasts ≤30s before the next disk read refreshes the cache. |
| Merged hook (intent-sdlc) fails → no SDLC context injected | Outer guard exits 0; Claude proceeds without context — same as current graceful degradation |
| 3-agent audit misses findings that 5-agent caught | Synthesis agent explicitly instructed to flag coverage gaps; Security dimension unchanged |
| Haiku impl-reviewer insufficient for complex implementation review | Haiku handles checklist matching; deep logic review is Claude's primary task, not the reviewer's |
| Uncapped parallel in zie-implement causes API rate limit | Rate limit results in organic throttle by Claude Code; `depends_on` still prevents file conflicts |
| plans/archive grows unbounded over time | Manual `make archive-plans` only; no auto-archive risk |

---

## Out of Scope

- Removing safety checks or security validations (regex safety-check.py unchanged)
- Changing SDLC pipeline stages or quality gates
- Changing model tier philosophy (Haiku/Sonnet/Opus ranking unchanged)
- zie-memory integration changes
- Auto-archiving plans on schedule
- Applying optimizations to projects that use zie-framework as a plugin (template changes only affect new `/zie-init` installs; existing projects must opt in manually)
