---
tags: [feature]
---

# Parallel Pipeline Stages

## Problem

Backlog → spec → plan → review stages run sequentially today. When multiple items are in the pipeline (e.g., sprint batch), each stage blocks on the previous one even when items are independent. Reviews are especially slow since each spawns a forked subagent.

## Motivation

Speed matters for a solo developer iterating fast. Independent items can have their specs drafted in parallel, plans written in parallel, and reviews run concurrently. The key constraint: parallelism must save wall-clock time without blowing token budget — launching 5 subagents that each read the full codebase is faster but 5x the tokens. The design must balance speed vs. token cost.

## Rough Scope

- Analyze which pipeline stages can safely run in parallel for independent items
- Implement parallel spec drafting (multiple items → concurrent spec-design calls)
- Implement parallel plan writing (multiple specs → concurrent write-plan calls)
- Implement parallel reviews (multiple specs/plans → concurrent reviewer calls)
- Add token-aware throttling: cap concurrent subagents to avoid token explosion
- Keep WIP=1 enforcement for implementation — parallelism is for pre-implementation stages only