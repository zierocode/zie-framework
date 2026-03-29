---
approved: true
approved_at: 2026-03-30
backlog: backlog/zie-audit-v2.md
---

# zie-audit v2 — Design Spec

**Problem:** `/zie-audit` finds defects but not improvement opportunities. Missing
dimensions (Performance, Dependency Health, Observability) and no external research
pass mean projects miss ecosystem-specific upgrades. Phase 3 wastes an agent call
on synthesis; Phase 4 wastes user time on one-by-one prompts.

**Approach:** Add a 4th parallel agent dedicated to stack/domain-driven external
research. Consolidate 6 dimensions into 3 combined agents. Make Phase 3 inline
synthesis (no extra agent). Batch Phase 4 prompts. All research driven by
detected `{stack}` and `{domain}` — no hardcoded language assumptions.

**Components:**
- `commands/zie-audit.md` — full rewrite
- `tests/unit/test_zie_audit_v2.py` — new test file (20 assertions)

**Data Flow:**

1. Phase 1 (inline): read manifests → build stack/domain/deps bundle; read
   ROADMAP backlog slugs + ADR slugs for dedup; run `git log --oneline -15`
2. Phase 2 (4 parallel agents):
   - Agent 1: Security + Dependency Health (6 WebSearch)
   - Agent 2: Code Health + Performance (2 WebSearch)
   - Agent 3: Structural + Observability (2 WebSearch)
   - Agent 4: External Research — improvement-focused, `{stack}`/`{domain}` queries (6 WebSearch)
3. Phase 3 (inline): filter existing backlog/ADRs → dedup → score → categorize
   (Quick Win / Strategic / Defer) → rank → print report
4. Phase 4: batch prompt CRITICAL then HIGH (all / select / skip) → create
   backlog files → update ROADMAP Next

**Edge Cases:**
- No `zie-framework/` dir: skip ROADMAP/ADR dedup, proceed with full findings
- Agent timeout: proceed with results from completed agents, note missing dimension
- Zero CRITICAL/HIGH findings: print "No high-priority findings" and skip Phase 4
- All findings already in backlog: print "All findings already tracked"

**Out of Scope:**
- Auto-fix suggestions (out of audit scope — that's /zie-fix)
- Trend comparison with previous audit reports
- Per-file blame / git history analysis
