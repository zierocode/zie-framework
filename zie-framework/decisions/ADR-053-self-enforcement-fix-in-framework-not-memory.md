# ADR-053 — Self-Enforcement: Fix Bad Patterns in Framework Spec, Not Memory

**Status:** Accepted

## Context

During the v1.18.1 sprint, a bad pattern (redundant test runs: running
`make test-unit` 3× with no code change between runs, just to grep the output
differently) was caught by Zie. The instinct was to save a memory entry.
Zie corrected: "มันควรต้องแก้ที่ framework สิ ไม่ใช่ memory" — fix in the
framework, not memory.

## Decision

When a harmful AI behavior pattern is identified during development (redundant
test runs, redundant file reads, unnecessary looping), the fix goes into the
relevant `commands/*.md` or `skills/*/SKILL.md` as an explicit rule — not into
session memory. Framework specs are loaded fresh every run and enforced on
every agent session. Memory is conversational and session-scoped.

## Consequences

**Positive:** Fixes are durable — any agent running the command encounters the
rule without needing prior context. Framework specs self-document the
constraints. Pattern matches how the framework already handles other behavioral
rules (TDD discipline, WIP=1 enforcement, etc.).

**Negative:** Requires a code change (Edit to a spec file) instead of a quick
memory save. The fix must be precise enough that it doesn't break structural
tests.

**Neutral:** Memory still appropriate for user preferences and one-session
context. Framework specs appropriate for repeatable AI behavioral constraints.

## Alternatives

- Memory-only (rejected: session-scoped, not durable across new conversations)
- CLAUDE.md global rule (considered: only appropriate for universal constraints,
  not command-specific behavior)
