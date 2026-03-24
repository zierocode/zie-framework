# Reviewer Terse Output

## Problem

All three reviewers (spec-reviewer, plan-reviewer, impl-reviewer) produce
verbose output even for simple verdicts. An approval message often runs 3–5
sentences describing what passed. Issues output includes prose framing around
each bullet. Every reviewer invocation adds unnecessary tokens to the context
window regardless of outcome.

## Motivation

Reviewer output is consumed by the calling command and by Claude's working
context. Terse output reduces the per-review token cost without losing any
information — a reviewer verdict is binary (approved/issues) and the value
is in the specific findings, not the framing around them.

## Rough Scope

- Approval output: exactly one line — `✅ APPROVED`
- Issues output: `❌ Issues Found` header + numbered bullet list only —
  no prose introduction, no closing instructions beyond the fix prompt
- Apply to spec-reviewer, plan-reviewer, and impl-reviewer uniformly
- Out of scope: changing what is checked; changing iteration logic
  (see reviewer-fail-fast)
