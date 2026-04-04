# zie-retro: Inline ADR Writing + ROADMAP Update Instead of Parallel Agents

## Problem

`commands/zie-retro.md:94-99` spawns 2 parallel background Agents for (1) writing ADR files and (2) updating the ROADMAP Done section. Both tasks are deterministic file writes (≤5 ADRs per retro, one ROADMAP edit). The agent spawn serializes large context bundles (`done_section_current`, `decisions_json`, `shipped_items`) into each subprompt, paying 1k-2k tokens of context serialization overhead per agent for work that could be done inline in seconds.

## Motivation

Subagents are valuable for independent reasoning tasks. Writing 3 ADR files and appending a Done entry is deterministic structured output — no reasoning needed. Inline execution is faster (no agent spawn latency), cheaper (no context serialization), and more predictable. The parallel agents were added for speed but for ≤5 files the spawn overhead likely dominates.

## Rough Scope

- Replace the 2 parallel Agent spawns in `zie-retro.md` with inline Write/Edit operations
- Write ADR files directly from the retro command's context
- Update ROADMAP Done section inline
- Remove `run_in_background: true` scaffolding for these two tasks
