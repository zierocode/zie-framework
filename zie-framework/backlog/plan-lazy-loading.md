# Plan Lazy Loading

## Problem

`/zie-implement` reads the entire plan file at startup — including full code
blocks for every task. A plan with 8 tasks and complete code per step can be
hundreds of lines loaded into context before any work starts. Tasks 4–8 are
irrelevant until tasks 1–3 are done.

## Motivation

Most of the plan file is not needed until the relevant task begins. Loading
only the header (Goal, Architecture, task name list) at startup and the full
task detail only when that task becomes active cuts the plan's context
footprint by 60–80% for multi-task features.

## Rough Scope

- `/zie-implement` startup: read plan header + task names only (first ~20 lines)
- Before starting Task N: read that task's full section (Acceptance Criteria,
  files, RED/GREEN/REFACTOR steps)
- Out of scope: changing the plan file format; lazy loading for /zie-plan
  approval (user needs to see the full plan there)
