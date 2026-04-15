---
tags: [feature]
---

# Deeper Thinking in Backlog Spec Plan

## Problem

Current backlog/spec/plan phases transcribe user input rather than think ahead — they capture what's said but don't surface blind spots, edge cases, or downstream implications. The user has to notice gaps themselves and come back to fix them, which wastes iteration cycles.

## Motivation

A solo developer benefits most when the framework acts as a thinking partner, not a stenographer. Proactively flagging risks, suggesting alternatives, and considering non-obvious impacts during backlog → spec → plan means fewer review-reject-fix cycles and higher-quality artifacts on first pass. Lean: add depth without adding process steps.

## Rough Scope

- Backlog: after capturing user's idea, suggest 2-3 additional considerations the user might have missed (edge cases, dependencies, risks)
- Spec: think through failure modes, alternatives, and "what if" scenarios proactively — not just structure what the user described
- Plan: consider task ordering risks, hidden dependencies, and rollback strategies — not just decompose the spec
- All phases: keep output concise — depth in thinking, not verbosity in writing