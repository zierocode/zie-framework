# Spec: Retro Inline Format — Remove Background Agents for Text-Processing Steps

Date: 2026-04-04
Status: Draft
Author: Zie

---

## Problem

`/zie-retro` spawns two background agents (`retro-format`, `docs-sync-check`) purely
for text-processing tasks — reasoning over `compact_json` and reading/comparing files.
Neither agent writes any files. Background agents add latency, TaskCreate/TaskUpdate
overhead, and an extra failure surface for work that Claude can do inline as a
reasoning step. This violates the principle: only spawn agents when they need to write
files or perform isolated, long-running work.

---

## Goal

Eliminate the two text-processing background agents. Replace them with inline reasoning
steps inside `/zie-retro`. Keep the two file-writing agents (ADR writer, ROADMAP updater)
unchanged.

---

## Approach A — Full Inline Replacement (selected)

### 1. retro-format → inline reasoning step

Remove the `Agent(subagent_type="general-purpose", run_in_background=True, ...)` call
for retro formatting. Instead, after building `compact_json`, Claude formats the five
retro sections directly as a reasoning step:

```
Given compact_json, produce five sections:
1. สิ่งที่ Ship ออกไป — list shipped features/fixes from compact_json.shipped
2. สิ่งที่ทำงานได้ดี — what worked well (infer from context)
3. สิ่งที่เจ็บปวด — pain points (infer from context + compact_json.pain_points)
4. การตัดสินใจสำคัญ — key decisions from compact_json.decisions
5. Pattern ที่ควรจำ — reusable techniques worth storing

Print output immediately. No Agent call, no TaskCreate.
```

Section structure and content remain identical to the current `retro-format` skill output.

### 2. docs-sync-check → inline Glob + Read + compare block

Remove the `Agent(subagent_type="general-purpose", run_in_background=True, ...)` call
for docs-sync checking. Replace with an inline block in the command:

```
**Docs-sync skip guard:** if `git log -1 --format="%s"` starts with `release:` →
  print "Docs-sync: skipped (ran during release)" and skip this block entirely.

Otherwise, run inline:
1. Glob `commands/*.md` → collect command names (strip .md)
2. Glob `skills/*/SKILL.md` → collect skill parent dirs
3. Glob `hooks/*.py` → collect hook filenames (exclude utils.py)
4. Read CLAUDE.md — check Development Commands section and skills table
5. Read README.md — check commands/skills tables
6. Compare actual vs. documented:
   - missing_from_docs: on disk but not in docs
   - extra_in_docs: in docs but not on disk
7. Print verdict:
   - If in sync: "CLAUDE.md in sync | README.md in sync"
   - If stale: update CLAUDE.md and/or README.md inline, print
     "Updated CLAUDE.md: added <X>, removed <Y>" / "Updated README.md: ..."
```

The `release:` prefix skip guard from the current command is preserved exactly.

### 3. ADR writer agent — unchanged

`Agent(subagent_type="general-purpose", run_in_background=True, ...)` for writing
ADR files remains. It writes files to `zie-framework/decisions/` — justifies agent use.

### 4. ROADMAP updater agent — unchanged

`Agent(subagent_type="general-purpose", run_in_background=True, ...)` for updating
`zie-framework/ROADMAP.md` Done section remains. It writes a file — justifies agent use.

### 5. Skill deprecation

Mark `zie-framework:retro-format` and `zie-framework:docs-sync-check` as deprecated.
Add deprecation notice to each skill's `SKILL.md` frontmatter and body. Do NOT delete
the skill files — they serve as fallback documentation and may be referenced in tests.

Deprecation notice to add:

```yaml
# In frontmatter:
deprecated: true
deprecated_since: "2026-04-04"
deprecated_reason: "Logic inlined into /zie-retro command. Skill no longer called."
```

And in the body (top of file, below frontmatter):

```
> **DEPRECATED** (2026-04-04): This skill is no longer invoked by /zie-retro.
> The retro-format / docs-sync logic is now inlined directly in the command.
> Kept for reference only. Do not invoke.
```

---

## Files Changed

| File | Change |
| --- | --- |
| `commands/zie-retro.md` | Remove two background agent calls; add inline retro-format reasoning step; add inline docs-sync Glob+Read+compare block |
| `skills/retro-format/SKILL.md` | Add deprecation notice (frontmatter + body) |
| `skills/docs-sync-check/SKILL.md` | Add deprecation notice (frontmatter + body) |

No new files. No file deletions.

---

## Acceptance Criteria

| # | AC |
| --- | --- |
| AC-1 | `/zie-retro` spawns zero background agents for text-processing steps (retro-format and docs-sync-check). Read `commands/zie-retro.md` and confirm no `Agent(` call exists for these two tasks. |
| AC-2 | Retro output still contains all five sections in Thai: สิ่งที่ Ship ออกไป, สิ่งที่ทำงานได้ดี, สิ่งที่เจ็บปวด, การตัดสินใจสำคัญ, Pattern ที่ควรจำ. |
| AC-3 | ADR entries still use the 5-section format (Status, Context, Decision, Consequences, Alternatives) and are still written by an Agent call. |
| AC-4 | Docs-sync verdict still appears in retro output (either in-sync message or updated-files message). |
| AC-5 | The `release:` prefix skip guard for docs-sync is preserved in the command. |
| AC-6 | ROADMAP Done-section update is still performed by an Agent call (file-writing justified). |
| AC-7 | `skills/retro-format/SKILL.md` contains deprecation notice in frontmatter and body. |
| AC-8 | `skills/docs-sync-check/SKILL.md` contains deprecation notice in frontmatter and body. |
| AC-9 | The fallback comment `<!-- fallback: if Agent unavailable ... -->` is removed entirely — deprecated skills must not be called as fallbacks after this change. |

---

## Testing

Not applicable — this is a command file change (Markdown). No Python code is added or
modified; no pytest tests exist for command prose.

AC verification method: read `commands/zie-retro.md` after implementation and confirm:
- No `Agent(` call present for retro-format or docs-sync-check tasks
- Inline retro-format block present with 5-section headings
- Inline docs-sync Glob+Read+compare block present with `release:` skip guard
- `Agent(` calls still present for ADR writer and ROADMAP updater

---

## Out of Scope

- Changing the ADR writer or ROADMAP updater agents
- Deleting the deprecated skill files
- Modifying hook behavior
- Changing the `compact_json` structure
- Altering the brain store or memory steps
