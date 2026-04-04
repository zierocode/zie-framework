# zie-plan: Trim Redundant Notes Section

## Problem

`commands/zie-plan.md:173-181` has a Notes section that restates: plan file path format, spec match glob, what "pending" and "approved" mean, and the reviewer/rejection flow. All of these are already defined precisely in the command body. The Notes section adds ~9 lines of pure redundancy.

## Motivation

Every token in a command file is loaded into context on invocation. Removing 9 lines of redundant prose directly reduces the per-invocation token cost of `/zie-plan`. Small but zero-effort gain.

## Rough Scope

- Delete the Notes section from `commands/zie-plan.md` (lines 173-181)
- Verify no information is lost (all content is defined inline in the command body)
