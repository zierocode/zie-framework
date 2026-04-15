# command-compress-batch

## Problem

Four command files (sprint, status, retro, release) contain verbose prose that can be compressed by 15-25% without losing functionality. Each file follows the same pattern: long instructional text that can be shortened using tables, inline references, and removing redundant explanations.

## Rough Scope

- Compress `commands/sprint.md` — reduce word count by ~20%
- Compress `commands/status.md` — reduce word count by ~15%
- Compress `commands/retro.md` — reduce word count by ~15%
- Compress `commands/release.md` — reduce word count by ~20%
- Follow compression patterns established in v1.20.0 (argument tables, inline guidance, template extraction)
- Maintain all functional behavior — only reduce token cost

## Priority

MEDIUM — efficiency improvement, no new features

## Merged From

- command-compress-sprint
- command-compress-status
- command-compress-retro
- command-compress-release

Reason: All four touch command markdown files with the same compression technique. Each takes < 15 min. No spec or plan exists for any.