---
tags: [feature]
---

# Wire Simplify Step Conditionally After GREEN Phase in /implement

## Problem

After the GREEN phase (tests pass), the implementation is functionally correct but
may have leftover scaffolding, duplicated logic, or verbose code from the TDD
red-green cycle. There is currently no automated quality gate that catches
over-engineered or redundant code before REFACTOR/commit. The `simplify` skill
exists in the framework but is never invoked by the SDLC workflow.

## Motivation

AI-assisted simplification after GREEN is a recognized best practice (IBM, Augment
Code, Tabnine all include a post-implement refactor pass). Research shows it reduces
Class LoC by a median of 15 lines per file and improves review pass rates from
55% → 81% (Qodo 2025). Adding it conditionally — only when the line delta is
significant — avoids overhead for small fixes while capturing real gains on
multi-file features.

## Rough Scope

- In `commands/implement.md` REFACTOR phase: after GREEN confirmed, check
  `git diff --stat HEAD` line delta for changed files
- If total lines changed > 50 → invoke `Skill(code-simplifier:code-simplifier)`
  on recently modified files
- If lines changed ≤ 50 (small patch / hotfix) → skip simplify pass silently
- Never invoke for tasks marked `priority: low` or tagged `hotfix`
- Document the threshold (50 lines) as a configurable constant
- Tests: verify simplify is invoked only when threshold exceeded
