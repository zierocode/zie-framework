---
description: Verify CLAUDE.md and README.md are in sync with commands/skills/hooks on disk. Returns claude_md_stale and readme_stale verdicts.
background: true
allowed-tools: Read, Glob, Grep
---

# docs-sync agent

Invoke `Skill(zie-framework:docs-sync)` with the list of changed files
passed in `$ARGUMENTS` by `/retro` or `/release`.

Return a JSON verdict:
```json
{"claude_md_stale": false, "readme_stale": false, "notes": ""}
```
