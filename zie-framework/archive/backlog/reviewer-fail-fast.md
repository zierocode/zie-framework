# Reviewer Fail-Fast — All Issues in One Pass

## Problem

The current reviewer loop runs up to 3 iterations: reviewer finds issue →
fix → re-invoke reviewer → reviewer finds another issue → fix → re-invoke.
Each round trip is a full model call. A reviewer that surfaces issues one at
a time forces unnecessary back-and-forth.

## Motivation

A reviewer that returns all issues in a single pass lets the developer fix
everything at once, then run one final verify pass. This cuts reviewer
round-trips from up to 3 per-issue to 2 total (initial scan + final confirm),
regardless of how many issues are found.

## Rough Scope

- Update spec-reviewer, plan-reviewer, and impl-reviewer prompts to explicitly
  surface ALL issues found in a single response — not just the first or most
  critical
- Change the iteration pattern in `/zie-plan` and `/zie-implement`: initial
  review pass → developer fixes all → one final "confirm fixed" pass → done
- Max iterations drops from 3 per-issue to 2 total per review cycle
- Out of scope: changing what reviewers check; model selection (see
  model-haiku-fast-skills); persistent reviewer memory (see
  reviewer-agents-memory)
