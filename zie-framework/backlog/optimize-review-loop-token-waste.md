---
tags: [debt]
---

# Optimize Review Loop Token Waste

## Problem

Spec and plan review loops re-spawn a forked subagent on every confirm pass, causing the reviewer to re-read all files from scratch and re-process the full context_bundle (ADRs + project context) each time — even though ADRs and project context haven't changed between iterations.

## Motivation

Each confirm pass costs ~50-70% of the initial review's tokens because the forked subagent starts completely fresh: re-loading SKILL.md instructions, re-processing context_bundle, re-doing Grep/Glob searches. For a solo developer iterating quickly, this is the biggest token sink in the pipeline. Inline confirm passes (caller verifies fixes itself after reviewer pass 1) eliminate this overhead entirely.

## Rough Scope

- Modify `spec-design` SKILL.md: after reviewer returns Issues Found → fix issues → verify inline (no subagent re-invocation)
- Modify `/plan` command: same inline confirm pattern
- Keep `context: fork` for the initial review pass (pass 1) — isolation still valuable there
- Remove confirm pass (pass 2) subagent invocation from both flows

⚠ Similar item existed: `review-loop-optimization` (v1.28.2) — that addressed a different aspect (subagent context guard). This item targets the confirm-pass re-invocation waste specifically.