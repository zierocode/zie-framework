# ADR-017: impl-reviewer Upgraded from haiku/low to sonnet/medium

Date: 2026-03-24
Status: Accepted

## Context

`impl-reviewer` ran on `model: haiku, effort: low`. Code review is a
reasoning-heavy task: the reviewer must detect subtle logic errors, missing
edge cases, and spec violations — not just enumerate facts. Haiku was
under-powered for this. The skill already uses `context: fork`, which bounds
input to the changed-files bundle only (typically 3-10 files × 200 lines),
so the cost of upgrading is contained.

## Decision

Upgrade `impl-reviewer` to `model: sonnet, effort: medium`. Leave all other
reviewer skills (spec-reviewer, plan-reviewer) on haiku — they review
structured documents where enumeration is sufficient.

## Consequences

**Positive:** Code review quality improves for the primary regression-prevention
gate. Fork isolation means sonnet sees only the bounded changed-files bundle,
not the full session context — cost per review is predictable (≈ 2-5× haiku
but bounded by changed-file count, not session length).
**Negative:** Slightly higher cost per `/zie-implement` task that triggers a
review. LOW-risk tasks skip the reviewer entirely, so the increase is bounded
to HIGH-risk tasks only.
**Neutral:** `EXPECTED_HAIKU` test list updated to exclude impl-reviewer.
