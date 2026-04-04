---
slug: audit-readme-dir-fix
status: approved
date: 2026-04-01
---
# Spec: Fix Doubled Path and Wrong Comment in README Directory Structure

## Problem

`README.md` line 106 (inside the Directory Structure code block) reads:

```text
│   │   └── project/context.md  # ADR log (append-only)
```

This appears under the `project/` tree node, making the implied path
`zie-framework/project/project/context.md` — a doubled `project/` component.
The actual path on disk is `zie-framework/project/context.md`.

Additionally, the inline comment `# ADR log (append-only)` is wrong. ADR files
live in `zie-framework/decisions/`. `context.md` is the project context file
(background, goals, constraints) — not an ADR log.

## Proposed Solution

Two targeted corrections to the Directory Structure code block in `README.md`:

1. Remove the spurious `project/` prefix so the entry reads `context.md`.
2. Update the inline comment from `# ADR log (append-only)` to
   `# project context (background, goals, constraints)`.

No other paths in the section are wrong. The resulting line:

```text
│   │   └── context.md          # project context (background, goals, constraints)
```

## Acceptance Criteria

- [ ] AC1: `README.md` directory structure block no longer contains
  `project/context.md`; it reads `context.md` instead.
- [ ] AC2: The inline comment for `context.md` accurately describes the file
  (not "ADR log").
- [ ] AC3: All other paths in the Directory Structure block are unchanged.
- [ ] AC4: No other files are modified (pure README docs fix).

## Out of Scope

- Renaming or moving `context.md` on disk.
- Changes to any hook, command, skill, or template files.
- Updating `decisions/` entries or any other ADR content.
- Linting or reformatting the rest of `README.md`.
