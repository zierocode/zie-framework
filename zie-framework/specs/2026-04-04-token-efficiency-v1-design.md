---
approved: true
approved_at: 2026-04-04
backlog: backlog/token-efficiency-v1.md
---

# Token Efficiency v1 — Design Spec

**Problem:** zie-framework over-spends tokens in three areas: reviewers load all 55+ ADR files on every pipeline pass (~3,000–8,000 tokens per run), CLAUDE.md has dynamic content near the top that busts CC's system-prompt cache prefix on every release, and skill/command prompts retain residual verbosity after the v1.19.0 lean sprint.

**Approach:** Three targeted fixes applied in sequence — (A) ADR Summary Gate: reviewers read only a compact one-line-per-ADR index by default and fetch a full ADR only when a conflict is flagged; (B) CLAUDE.md reorder: stable structural content moves to the top (maximum cacheable prefix), dynamic version content moves to the bottom; (C) systematic word-count-gated trim of all 26 skill/command files, test-protected throughout.

**Components:**
- `skills/load-context/SKILL.md` — summary-first ADR load protocol
- `skills/reviewer-context/SKILL.md` — summary-first ADR load protocol
- `skills/spec-reviewer/SKILL.md` — inline fast-path updated to use summary
- `skills/plan-reviewer/SKILL.md` — inline fast-path updated to use summary
- `skills/impl-reviewer/SKILL.md` — inline fast-path updated to use summary
- `zie-framework/decisions/ADR-000-summary.md` — reformatted as 1-line-per-ADR index (≤300 tokens total)
- `commands/retro.md` — add haiku pass to auto-update ADR-000-summary.md post-release
- `CLAUDE.md` — reordered with `<!-- STABLE -->` / `<!-- DYNAMIC -->` marker comments
- All 12 `skills/*/SKILL.md` files — word count audit + compression
- All 14 `commands/*.md` files — word count audit + compression

**Data Flow:**

*A — ADR Summary Gate:*
1. `reviewer-context` / `load-context` invoked → read `ADR-000-summary.md` only (~300 tokens)
2. Conflict check: reviewer reads summary title + one-line decision for each ADR; if any entry is topically relevant to the current spec/plan under review, load that specific full ADR file from disk
3. No relevant ADRs found in summary → proceed with summary content only; skip all `decisions/ADR-*.md` reads
4. `/retro` completes → haiku subagent appends new ADRs from session to `ADR-000-summary.md` (one line each)
5. Fast-path preserved: `context_bundle` pass-through still works; caller-provided bundle bypasses disk entirely

*B — CLAUDE.md Cache Structure:*
1. Reorder sections: [Project Structure → Key Rules → Hook Ref Docs → Agent mode] (stable) then [Tech Stack + version → optional dep notes] (dynamic)
2. Add `<!-- STABLE: do not move below dynamic section -->` before stable block
3. Add `<!-- DYNAMIC: version-specific, ok to change -->` before dynamic block
4. On each future release, version bump touches only the DYNAMIC section → cache prefix unchanged

*C — Skill/Command Compression:*
1. Baseline: `wc -w` all 26 files → record in commit message
2. Per file: remove redundant phase headers, fallback restatements, Notes sections that restate rules, verbose output format prose
3. Keep: checklists, required steps, format specifications, any line with a test assertion
4. Grep test suite before removing any line (per established protocol)
5. `make test-unit` after each file batch → gate before moving to next
6. Final: `wc -w` again → confirm 20–30% reduction per file

**Edge Cases:**
- `ADR-000-summary.md` missing → fall back silently to loading all `decisions/ADR-*.md` (current behavior); emit `[zie-framework] ADR summary missing — using full load` to stderr
- Conflict flagged in summary but full ADR load doesn't resolve it → surface issue to reviewer as usual
- CLAUDE.md reorder breaks a test → grep test assertions for section ordering before committing
- Skill trim accidentally removes a test-enforced line → caught by `make test-unit` gate

**Out of Scope:**
- Changing what any skill or command does functionally
- Removing acceptance criteria, checklist items, or output format specs
- API-level `cache_control` headers (requires direct Anthropic API calls, not applicable to CC plugin)
- Automating CLAUDE.md reorder (one-time manual change)
- Trimming hook Python files (separate concern)
