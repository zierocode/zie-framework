---
date: 2026-04-15
status: approved
slug: command-compress-batch
---

# command-compress-batch — Compress 4 Command Markdown Files

## Problem

Four command files (sprint 2108w, status 865w, retro 1181w, release 769w — total 4923w) contain verbose prose that adds token cost per invocation. Each follows the same pattern: long instructional sections that can be shortened without losing functional behavior.

## Solution

Apply three compression patterns established in v1.20.0:

1. **Tables for structured data** — convert multi-paragraph descriptions of arguments, gates, or steps into compact tables with columns for name/type/default/description.
2. **Inline references** — replace repeated explanatory prose with `Skill(name)` calls or `see /command` cross-references; keep only the novel logic.
3. **Template extraction** — move long code blocks (python snippets, bash sequences) into shared templates or one-liner invocations; reference by name.

Target: 15-25% word reduction per file, functional behavior unchanged.

## Rough Scope

| File | Current | Target | Reduction |
| --- | --- | --- | --- |
| sprint.md | 2108w | ~1680w | ~20% |
| status.md | 865w | ~735w | ~15% |
| retro.md | 1181w | ~1005w | ~15% |
| release.md | 769w | ~615w | ~20% |

## Files Changed

- `commands/sprint.md`
- `commands/status.md`
- `commands/retro.md`
- `commands/release.md`