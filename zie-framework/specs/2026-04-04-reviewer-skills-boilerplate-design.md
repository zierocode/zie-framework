# Spec: Reviewer Skills Phase 1 Boilerplate Extraction

status: draft
backlog: zie-framework/backlog/reviewer-skills-boilerplate.md

## Problem

All three reviewer skills (`spec-reviewer`, `plan-reviewer`, `impl-reviewer`) contain a
nearly identical 30-line "Phase 1 — Load Context Bundle" block covering: `context_bundle`
conditional, ADR cache loading, `project/context.md` read, and `ROADMAP.md` read.
This is 90 lines of duplicated prose that must be kept in sync. Any change to the caching
protocol (e.g. `adr_cache_path`, cache helper signatures) requires three separate edits
with risk of drift.

## Solution

**Option A (chosen):** Extract the shared Phase 1 logic into a new canonical skill:
`skills/reviewer-context/SKILL.md`. Each reviewer skill replaces its inline Phase 1 block
with a one-line invocation reference: `Invoke reviewer-context skill to load shared context`.

The `reviewer-context` skill is `user-invocable: false`, `context: fork`, read-only
(`allowed-tools: Read, Grep, Glob`), and returns a structured context object (`adrs_content`,
`context_content`) that the calling reviewer uses in its Phase 2+ checklist.

**Why not Option B (document-only pattern):** A document reference still leaves 90 lines
of duplicated prose in production skill files. It solves the maintenance problem on paper
but not in practice.

**Constraint — test suite strings must be preserved:** The existing test suite asserts
specific strings directly in each reviewer SKILL.md:
- `"if context_bundle provided"` (all three reviewers)
- `"context_bundle.adrs"` / `"context_bundle.context"` (spec + plan reviewers)
- `"adr_cache_path"` (impl-reviewer)
- `"decisions/*.md"` / `"project/context.md"` (all three)
- `"ROADMAP"` (spec + plan reviewers)

These strings must remain present in each reviewer SKILL.md — either inline or via a
stub that satisfies the assertions. The Phase 1 block in each reviewer is replaced with
a short invocation stub that retains the required keywords, plus a pointer to
`reviewer-context` for full protocol details.

## Acceptance Criteria

1. `skills/reviewer-context/SKILL.md` exists and contains the full shared Phase 1 logic
   (context_bundle conditional, ADR cache load, `project/context.md`, `ROADMAP.md`).
2. Each of the three reviewer SKILL.md files has its Phase 1 block replaced with a
   concise invocation stub (`Invoke reviewer-context`) that retains all test-required strings.
3. `make test-fast` passes with zero failures after the change (no test regressions).
4. `make lint` passes.
5. Each reviewer SKILL.md is shorter by at least 20 lines compared to pre-change.
6. `reviewer-context` is `user-invocable: false` — not exposed as a standalone command.
7. `impl-reviewer` stub retains `adr_cache_path` reference (its Phase 1 differs from the
   other two in that one field — the shared skill handles the common path, the stub
   documents the impl-specific variant).

## Out of Scope

- No Python hook changes — this is markdown-only.
- No changes to callers (`spec-design`, `write-plan`, `zie-implement`) — they already pass
  `context_bundle` correctly.
- No new tests required for the new skill file itself (existing tests cover the strings;
  a new existence test is added for `reviewer-context`).
- No changes to `context_bundle` protocol or ADR cache helpers.
