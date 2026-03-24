# Retro → Next Active Loop

## Problem

`/zie-retro` completes and stops — it doesn't close the loop back to the
backlog. The developer must manually decide what to pick up next, with no
nudge from what was just learned in the retrospective.

## Motivation

The E2E solo cycle should feel continuous: finish → reflect → start next.
Right now there is a dead stop after retro. Adding a final step that surfaces
the top candidate from the Next lane (weighted by priority and retro
learnings) closes the loop without adding complexity.

## Rough Scope

- After retro completes, surface top 1–3 items from the Next lane
- Weight by: priority (Critical first), then alignment with pain points
  identified in the retro
- Output a prompt: "Suggested next: X — run `/zie-plan X` to start"
- Out of scope: automatic plan creation, multi-item selection UI,
  dependency graph resolution
