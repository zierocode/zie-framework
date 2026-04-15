---
date: 2026-04-15
status: approved
slug: compact-output-lean
---

# Implementation Plan — compact-output-lean

## Steps

1. **`hooks/intent-sdlc.py`** — Replace `[zie-framework]` with `[zf]` in all `print()` and `json.dumps({"additionalContext": ...})` calls. Compact state suffix from `task:{active_task} | stage:{stage} | next:{suggested_cmd} | tests:{test_status}` to `now:{active_task} stage:{stage} next:{suggested_cmd} tests:{test_status}` (drop pipe separators, shorten `task:` → `now:`). Shorten intent line from `intent:{best} → {cmd}` to `intent:{best}→{cmd}` (drop spaces around arrow).

2. **`hooks/session-resume.py`** — Collapse the 4-line header block into 2 lines:
   - Line 1: `[zf] {project_name}({project_type}) v{version} | now:{active_label} | mem:{zie_memory_status}`
   - Line 2: `[zf] cmds: {command_list} | workflow: backlog→spec→plan→implement→release→retro`
   - Remove the separate "→ Run /status" line (redundant — `/status` is in cmds).
   - Shorten anti-patterns to: `[zf] anti: no direct spec/plan approval; reviewer first; no skip on "ทำเลย"`
   - Keep backlog nudge but compact: `[zf] backlog: {N} pending — /spec {first_slug}`
   - Keep staleness warning but prefix with `[zf]`.

3. **`commands/status.md`** — Replace verbose table headers with compact ones:
   - `| | |` → remove empty header rows, use inline `key: value` for single-entry rows.
   - Project info: single line `project: {name}({type}) v{version} | brain: {status} | drift: {N}`
   - Knowledge: `knowledge: ✓ synced | ⚠ drift | ? no baseline`
   - ROADMAP: `now: {N} | next: {N} | done: {N}`
   - Pipeline row: keep inline arrows but strip spaces: `backlog✓→spec✓→plan▶→release—→retro—`
   - Test table: `tests: unit:{status} int:{status} e2e:{status}`
   - Framework health: `config: safety={mode} mem={status} pw={status} drift={N}`
   - Stop failures: keep last 5 list but remove "Stop failures" label prefix — just bullet list under `failures:`.

4. **`commands/next.md`** — Minor: shorten header from `/next — recommended backlog items` to `/next` and compress output format: `{rank}. [{IMPACT}] {slug} (score:{N}) age:{age} | /spec {slug}` on one line per item.

5. **Dedup strings** — In `intent-sdlc.py`, update the dedup cache comparison strings to match the new compact format (already handled since we're changing the print strings).

6. **Update tests** — Fix any test assertions that check for `[zie-framework]` prefix or verbose labels in hook output.

## Tests

1. **Unit: intent-sdlc output format** — assert `[zf]` prefix on all emitted context lines; assert no `[zie-framework]` remains.
2. **Unit: session-resume output format** — assert header is ≤3 lines; assert `mem:` label present; assert no `Brain:` label.
3. **Unit: /status output** — regex check for compact format: `project:` line, `tests:` line, `pipeline:` line.
4. **Unit: /next output** — assert single-line format per item with `(score:` present.
5. **Integration: token count** — capture typical output before/after; assert ≥15% reduction in token estimate (split on whitespace, count tokens).

## Acceptance Criteria

- All hook output uses `[zf]` prefix (no `[zie-framework]` in stdout)
- session-resume header ≤3 lines
- `/status` output: project info on one line, tests on one line, pipeline inline
- `/next` output: one line per item
- Token reduction ≥15% on representative outputs (measured by whitespace-split count)
- All existing tests pass after string updates