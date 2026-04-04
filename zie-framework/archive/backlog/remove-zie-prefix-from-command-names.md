# Remove zie- prefix from command names

## Problem

Command names carry a redundant `zie-` prefix — e.g. `zie-fix.md` — making the
full invocation `zie-framework:zie-fix`. The namespace already identifies the plugin;
the prefix in the command name adds no value and creates visual noise.

## Motivation

Cleaner invocation surface: `zie-framework:fix`, `zie-framework:spec`,
`zie-framework:ship` read naturally. Aligns with standard CLI convention where
the command name is a plain verb, not a namespaced label. Reduces typo risk and
improves discoverability when users tab-complete or scan the plugin's command list.

## Rough Scope

**In:** Rename all 12 command files (`commands/zie-*.md` → `commands/*.md`).
Update all internal references — ROADMAP, CLAUDE.md, docs, skills, hooks, tests —
that reference the old command names.

**Out:** Skill names, hook script names, plugin.json metadata fields unrelated
to command invocation.
