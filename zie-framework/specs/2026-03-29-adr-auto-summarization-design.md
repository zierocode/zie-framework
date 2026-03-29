---
approved: true
approved_at: 2026-03-29
backlog: backlog/adr-auto-summarization.md
---

# ADR Auto-Summarization — Design Spec

**Problem:** Reviewer skills load all `decisions/*.md` on every invocation; at 24 ADRs / 914 lines today and growing ~1 ADR per release, the full ADR set will exceed practical context limits and waste tokens on history that has already been assimilated.

**Approach:** When `/zie-retro` counts more than 30 ADR files it generates `decisions/ADR-000-summary.md` — a single Markdown table compressing the oldest ADRs (all except the 10 most-recent) into one row each (ADR#, title, decision-in-one-line), then removes those individual files from `decisions/`. The three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) already load `decisions/*.md` in Phase 1; they are updated to load `ADR-000-summary.md` first when it exists, then load only the remaining individual ADR files. A `make adr-count` helper surfaces the current count for visibility. This approach is additive — reviewers continue to work identically when no summary exists — so the graceful-skip rule from ADR-006 is preserved.

**Components:**

- `commands/zie-retro.md` — add ADR count check + summary generation step after "Count ADR files" line
- `skills/spec-reviewer/SKILL.md` — update Phase 1 ADR loading to prefer `ADR-000-summary.md` + recent individual files
- `skills/plan-reviewer/SKILL.md` — same Phase 1 update
- `skills/impl-reviewer/SKILL.md` — same Phase 1 update
- `Makefile` — add `adr-count` target
- `tests/unit/test_adr_summarization.py` (Create) — unit tests for summary generation logic
- `zie-framework/decisions/ADR-000-summary.md` (Create at runtime, not source-tracked) — generated summary table

**Data Flow:**

1. `/zie-retro` counts files matching `zie-framework/decisions/ADR-*.md` (excluding `ADR-000-summary.md` itself)
2. Count <= 30 → skip summary step entirely; existing behaviour unchanged
3. Count > 30 → identify the oldest N ADRs to compress: all individual ADRs except the 10 most-recent (sorted by filename, which is `ADR-NNN-` prefix order)
4. For each ADR to compress: extract ADR number, title (first `# ` heading), and decision-in-one-line (first sentence of `## Decision` section)
5. Write `zie-framework/decisions/ADR-000-summary.md` — Markdown table with columns: ADR, Title, Decision
6. Delete each compressed individual file from `decisions/`
7. On next reviewer invocation, Phase 1 detects `ADR-000-summary.md` → reads it first, then reads remaining individual `ADR-*.md` files (the 10 most-recent)
8. Reviewer proceeds with full Phase 2 + Phase 3 checks using combined context

**Edge Cases:**

- Summary already exists when count re-crosses 30 threshold: overwrite `ADR-000-summary.md` with updated table; only newly-eligible ADRs (beyond current summary cutoff) are added; no duplicate rows
- Fewer than 11 total ADRs (count <= 10): keep-10-recent rule would compress nothing; skip generation even if count logic triggers
- `ADR-000-summary.md` present but individual files also still present (partially-generated state): reviewer reads both without error; summary row and full file for same ADR number results in duplication but not failure — idempotent re-run of retro step corrects state
- `## Decision` section missing from an ADR being compressed: use first non-heading paragraph as fallback; if none found, use `"(no decision text)"` placeholder
- Decision text extraction produces > 120 characters: truncate to 120 chars with trailing `…`
- `decisions/` directory missing: skip summary step; reviewer Phase 1 graceful-skip already handles this (ADR-006)
- `make adr-count` run when `decisions/` does not exist: print `0` and exit 0

**Out of Scope:**

- Summarizing specs, plans, or backlog files (ADR token cost is the stated problem)
- Automated summary generation outside of `/zie-retro` (hook or background agent trigger)
- Semantic deduplication of similar ADRs before summarization
- Configurable keep-N threshold via `.config` (30/10 constants are sufficient for now)
- Surfacing summary existence in `/zie-status` output
- Restoring compressed ADRs from git history (git is the source of truth; no restore command needed)
- Any changes to `archive/` structure defined in ADR-023 (that archive covers specs/plans/backlog, not decisions)
- Session-scoped ADR caching across multiple reviewer invocations (covered by separate `adr-session-cache` backlog item — that feature builds on top of the summary file produced here)
