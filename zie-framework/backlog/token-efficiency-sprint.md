---
id: token-efficiency-sprint
title: Token efficiency — trim prompts, cache regex, lean context
priority: medium
created: 2026-03-27
source: deep-analysis-2026-03-27
---

## Problem

~400–800 tokens wasted per session from:
1. Command prompts repeat title = description = first sentence (zie-implement, zie-release verbose intros)
2. Intent regex patterns recompiled on every hook invocation (not cached)
3. Roadmap cache miss = full file read each time
4. Skills frontmatter duplicates `zie_memory_enabled: true`, `model:`, `effort:` across 11 files

## Motivation

At Sonnet 4.6 medium effort, every token counts. Reducing prompt overhead directly reduces cost
and latency without sacrificing functionality.

## Acceptance Criteria

- [ ] `commands/zie-implement.md` intro trimmed — no redundant title/description repetition
- [ ] `commands/zie-release.md` intro trimmed
- [ ] `commands/zie-retro.md` intro trimmed
- [ ] Intent regex patterns compiled once (module-level constant) in `hooks/intent-sdlc.py`
- [ ] Redundant skill frontmatter fields defaulted in plugin.json or removed
- [ ] Token savings measured: before/after word count comparison documented in ADR or commit message

## Scope

- `commands/zie-implement.md`, `zie-release.md`, `zie-retro.md`
- `hooks/intent-sdlc.py` — compile patterns at module level
- `skills/*/SKILL.md` — remove redundant frontmatter where plugin.json can serve as default
