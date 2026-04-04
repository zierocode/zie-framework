---
name: reviewer-context
description: Load shared reviewer context (ADRs + project context + ROADMAP lanes). Called by spec-reviewer, plan-reviewer, and impl-reviewer Phase 1.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: ""
model: haiku
effort: low
---

# reviewer-context — Reviewer Context Loader

Shared Phase 1 protocol for all three reviewer skills. Loads ADRs, project
context, and ROADMAP lanes. Returns `adrs_content` and `context_content`.

## Steps

**Fast path** — if `context_bundle` provided by caller:
- `adrs_content` ← `context_bundle.adrs`
- `context_content` ← `context_bundle.context`
- Skip disk reads below.

**Disk fallback** — if `context_bundle` absent (backward-compatible):

1. **ADRs** — load via session cache (cache-first, summary-aware):
   - Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
     - Cache hit → use as `adrs_content`.
     - Cache miss → load from disk:
       - If `ADR-000-summary.md` exists → read first.
       - Read remaining `decisions/ADR-*.md` files; concatenate → `adrs_content`.
       - Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`.
   - Empty or missing `decisions/` → `adrs_content = "No ADRs found"`.

2. **Design context** — read `project/context.md` if it exists.
   Missing → `context_content = ""`.

3. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes.
   Missing → skip ROADMAP conflict check.

## Output

Returns `adrs_content` and `context_content` for the calling reviewer to use
in its review checklist.
