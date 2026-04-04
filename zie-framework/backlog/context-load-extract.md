# Extract Context-Bundle Load Pattern to Shared Skill

## Problem

The identical "Load Context Bundle" pattern (read `decisions/*.md`, call `write_adr_cache`, read `project/context.md`, assemble `context_bundle`) appears copy-pasted across `commands/zie-plan.md` (lines 73-88), `commands/zie-implement.md` (lines 44-49), and `commands/zie-sprint.md` (lines 102-113). Each copy is 10-15 lines of prose that inflates the individual command's token footprint and requires synchronized updates across 3 files on any protocol change.

## Motivation

A shared skill or clearly-documented pattern eliminates the maintenance surface and reduces each command's token footprint. Any change to the context-bundle protocol (e.g. new fallback level, new field) currently requires editing 3 files. One canonical source fixes this.

## Rough Scope

- Extract the context-bundle load block into a dedicated skill (e.g. `skills/load-context/SKILL.md`) or a well-documented reference section in PROJECT.md
- Replace the 3 inline copies with a `Skill(zie-framework:load-context)` call or a clearly-marked pointer
- Update tests for each affected command
