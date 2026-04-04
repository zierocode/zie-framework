# Spec: zie-init Delegate Scan to Explore Agent

**Date**: 2026-04-04
**Status**: Draft

## Problem

`/zie-init` Step 2 contains ~143 lines of pseudocode describing how to scan
an existing project and detect migration candidates. This scanning logic lives
in the parent command's markdown, making the command harder to read and
maintain. The scan itself is naturally an exploration task — a job for an
Explore subagent, not inline pseudocode.

## Goal

Replace Step 2's scanning pseudocode with a single `Agent(subagent_type=Explore)`
call. The parent command keeps only a compact summary of what to do with the
result. Sub-steps 2b–2i (decision and write logic) stay in the parent command
but are driven by a structured `scan_report` returned from the agent.

Target reduction: ≥100 lines from `commands/zie-init.md` Step 2.

## Explore Agent Prompt

The parent command invokes the agent with a self-contained prompt:

```
You are scanning an existing software project to help initialize zie-framework.

Scan the project at the current working directory. Read existing documentation
first as primary sources (they encode deliberate intent, not just structure):
  README.md, CHANGELOG.md, ARCHITECTURE.md, AGENTS.md,
  docs/**, **/specs/*.md, **/plans/*.md, **/decisions/*.md
  (exclude anything inside zie-framework/)

Then scan the codebase structure to fill in any gaps.

Exclude from all scans:
  node_modules/, .git/, build/, dist/, .next/, __pycache__/, *.pyc,
  coverage/, zie-framework/

Return ONLY a JSON object with this exact structure (no markdown, no prose):
The parent parser will extract JSON from the first '{' to the last '}' if explanation text is present — keep any explanation text before or after the JSON block.

{
  "architecture_pattern": "<string>",
  "components": [
    { "name": "<string>", "purpose": "<one-line string>" }
  ],
  "tech_stack": [
    { "name": "<string>", "version": "<string | null>" }
  ],
  "data_flow": "<string — entry point to response>",
  "key_constraints": ["<string>"],
  "test_strategy": {
    "runner": "<string | null>",
    "coverage_areas": ["<string>"]
  },
  "active_areas": ["<string — from git log --name-only -20>"],
  "existing_hooks": "<path to hooks/hooks.json if present, else null>",
  "existing_config": "<path to zie-framework/.config if present, else null>",
  "migration_candidates": {
    "specs":      ["<relative path>"],
    "plans":      ["<relative path>"],
    "decisions":  ["<relative path>"],
    "backlog":    ["<relative path>"]
  }
}

For migration_candidates: include files matching these patterns (relative to
project root), excluding anything already inside zie-framework/:
  specs:     **/specs/*.md, **/spec/*.md
  plans:     **/plans/*.md, **/plan/*.md
  decisions: **/decisions/*.md, **/adr/*.md, ADR-*.md (at project root)
  backlog:   **/backlog/*.md

For existing_hooks: check if hooks/hooks.json exists at project root.
For existing_config: check if zie-framework/.config exists.

If a field cannot be determined, use null for scalar fields or [] for arrays.
Do not invent information. Mark unknown scalars as null.
```

### Why self-contained

The agent prompt must not rely on any prior context from the parent command.
The parent passes the prompt and the agent returns a JSON blob. The parent
then drives all decisions from that blob.

## scan_report Structure

| Field | Type | Description |
| --- | --- | --- |
| `architecture_pattern` | `string` | e.g. `"MVC"`, `"Event-driven"` |
| `components` | `[{name, purpose}]` | Every significant module/package |
| `tech_stack` | `[{name, version}]` | Full stack with versions from config files |
| `data_flow` | `string` | Narrative from entry point to response |
| `key_constraints` | `[string]` | Real decisions in code/comments/docs |
| `test_strategy.runner` | `string\|null` | e.g. `"pytest"`, `"vitest"` |
| `test_strategy.coverage_areas` | `[string]` | Tested subsystems |
| `active_areas` | `[string]` | Paths active in recent git log |
| `existing_hooks` | `string\|null` | Path to `hooks/hooks.json` or `null` |
| `existing_config` | `string\|null` | Path to `zie-framework/.config` or `null` |
| `migration_candidates` | `{specs,plans,decisions,backlog}` | Arrays of relative paths per category |

### Failure modes

| Condition | Parent behaviour |
| --- | --- |
| Agent times out | Warn "Agent scan incomplete" → offer retry or greenfield fallback |
| Agent returns empty / non-JSON | Warn "Scan failed" → offer retry or greenfield fallback |
| `migration_candidates` key missing | Treat as all-empty arrays; continue |
| Individual path does not exist on disk | Skip that candidate silently |

## Output Parsing Strategy

The agent is instructed to return bare JSON (no markdown code block wrapper,
no surrounding prose). The parent parses with:

```python
scan_report = json.loads(agent_output.strip())
```

If the agent embeds explanation text despite the instruction, the parent
extracts the JSON by finding the first `{` and last `}` in the output:

```python
start = agent_output.index("{")
end   = agent_output.rindex("}") + 1
scan_report = json.loads(agent_output[start:end])
```

If neither parse succeeds, fall through to the "Agent returns empty /
non-JSON" failure path (warn + offer retry or greenfield fallback).

## How the Parent Command Uses scan_report

After the agent returns `scan_report`, Step 2 in the parent command does:

**2a** — Invoke Explore agent with the prompt above; receive `scan_report`.

**2b** — Draft the four knowledge files from `scan_report` fields:
  - `PROJECT.md` ← `architecture_pattern`, `components`, `tech_stack`
  - `project/architecture.md` ← `architecture_pattern`, `data_flow`, `active_areas`
  - `project/components.md` ← `components`
  - `project/context.md` ← `key_constraints` (unknowns marked TBD)

**2c** — Present all four drafts inline as markdown code blocks.

**2d** — Section-targeted revision loop (unchanged from current command).

**2e** — Write all four files to disk.

**2f** — Compute `knowledge_hash` via `python3 hooks/knowledge-hash.py`.

**2g** — Merge `knowledge_hash` + `knowledge_synced_at` into `.config`.
  `existing_config`: if non-null, the parent reads the file at that path and
  preserves any user-set values (e.g. `safety_check_mode`, timeouts) before
  writing the updated `.config`; if null, a fresh `.config` is created.

**2h** — Install or merge `hooks/hooks.json`, then present migration
  candidates from `scan_report.migration_candidates`.
  `existing_hooks`: if non-null, the parent treats hooks installation as a
  migration (merge strategy: preserve existing event handlers and add new
  ones); if null, the parent writes a fresh `hooks/hooks.json` directly.
  For migration candidates:
  - Skip if all arrays empty or key missing.
  - Filter: skip `README.md`, `CHANGELOG.md`, `LICENSE*`, `CLAUDE.md`,
    `AGENTS.md`, files already in `zie-framework/`, and any `docs/` tree
    with `index.md` or `_sidebar.md` at its root.
  - Validate each path exists on disk before presenting.
  - Prompt user: yes / no / select — migrate using `git mv`.

**2i** — Continue to Step 3.

The parent command Step 2 now reads as:

```
2. **Detect and scan existing project** (if existing — see greenfield check
   at top of step):

   a. Invoke Agent(subagent_type=Explore) with the scan prompt (see
      [Explore Agent Prompt] in spec). Receive `scan_report` JSON.
      On failure → warn + offer retry or greenfield fallback.

   b–i. Use scan_report to draft knowledge files, present for review,
        write to disk, compute knowledge_hash, present migration
        candidates. [Decision logic in sub-steps below.]
```

All scanning pseudocode is gone from the parent; it lives only in the agent's
self-contained prompt.

## Acceptance Criteria

1. `commands/zie-init.md` Step 2 is reduced by ≥100 lines compared to
   the current version (measured by line count diff).

2. Scan behaviour is **unchanged**: the agent detects the same signals as
   the current pseudocode — existing hooks (`hooks/hooks.json`), existing
   config (`zie-framework/.config`), migration candidates across all four
   categories (specs, plans, decisions, backlog).

3. The Explore agent prompt is **self-contained**: it does not rely on
   prior context from the parent command and can be executed independently.

4. The parent command still drives all **decisions** from `scan_report`
   (draft, review loop, write, hash, migrate) — no decision logic moves
   into the agent.

5. Failure handling is **preserved**: timeout → warn + offer retry;
   malformed JSON → warn + offer retry; missing `migration_candidates` →
   treat as empty and continue.

6. The `scan_report` JSON schema is documented in this spec and the
   agent prompt exactly matches it (field names, types, defaults).

7. The parent parses agent output as **bare JSON** using `json.loads(output.strip())`,
   with a fallback that extracts the first `{` … last `}` substring before
   retrying the parse. Only if both attempts fail does the parent fall through
   to the retry/greenfield-fallback path.

8. `existing_hooks` drives the **hooks installation strategy** in step 2h:
   non-null → merge; null → fresh write. `existing_config` drives the
   **config preservation strategy** in step 2g: non-null → read and preserve
   user-set keys; null → create fresh `.config`.
