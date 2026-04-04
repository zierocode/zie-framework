# Spec: Strip Static Boilerplate from Per-Event additionalContext
status: draft

## Problem

Three hooks inject static, session-invariant strings into `additionalContext` on
every event fire:

- **`failure-context.py`** — appends `"Quick fix: run \`make test-unit\` to
  reproduce; check output above for root cause."` to every tool-failure payload.
- **`sdlc-compact.py`** — emits `"[zie-framework] SDLC state restored after
  context compaction."` as the first line of every PostCompact payload.
- **`subagent-context.py`** — appends `"(see zie-framework/project/context.md)"`
  to every SubagentStart payload.

These strings are constants. They carry zero signal beyond what is already in
CLAUDE.md and are re-injected on every hook firing, consuming context tokens at
full cost each time.

## Solution

Move all static instructional/reference text to CLAUDE.md under a dedicated
**Hook Context Hints** section. Keep only genuinely dynamic runtime values in
each hook's `additionalContext` output.

### Changes per hook

| Hook | Remove (static) | Keep (dynamic) |
| ---- | --------------- | -------------- |
| `failure-context.py` | `"Quick fix: run \`make test-unit\` to reproduce; check output above for root cause."` | Active task, branch, last commit |
| `sdlc-compact.py` | `"[zie-framework] SDLC state restored after context compaction."` (PostCompact header) | Active task, now items, git branch, TDD phase, changed files |
| `subagent-context.py` | `"(see zie-framework/project/context.md)"` suffix | Feature slug, active task, ADR count |

### CLAUDE.md addition

Add a new section **Hook Context Hints** (after the existing Hook Configuration
table) with the three static strings as permanent project-level instructions:

```
## Hook Context Hints

On tool failure: run `make test-unit` to reproduce; check output above for root cause.
After context compaction: SDLC state is restored by the PostCompact hook.
In subagent context: ADR log lives at `zie-framework/project/context.md`.
```

## Acceptance Criteria

- [ ] `failure-context.py`: `context_string` does NOT contain the literal
  `"Quick fix:"` substring.
- [ ] `failure-context.py`: `context_string` still contains `Active task:`,
  `Branch:`, and `Last commit:` lines.
- [ ] `sdlc-compact.py` (PostCompact): output does NOT contain the literal
  `"SDLC state restored after context compaction"` string.
- [ ] `sdlc-compact.py` (PostCompact): output still includes active task, git
  branch, changed files, and TDD phase when present.
- [ ] `subagent-context.py`: payload does NOT contain the literal
  `"see zie-framework/project/context.md"` substring.
- [ ] `subagent-context.py`: payload still contains feature slug, active task,
  and ADR count.
- [ ] `CLAUDE.md` gains a **Hook Context Hints** section with all three removed
  strings as permanent instructions.
- [ ] All existing unit tests in `test_hooks_failure_context.py`,
  `test_hooks_sdlc_compact.py`, and `test_hooks_subagent_context.py` pass
  (updated to reflect removed static text).

## Out of Scope

- Removing or restructuring any dynamic content from hooks.
- Changing hook event routing or `hooks.json`.
- Modifying any templates or `/zie-init` behavior.
- Other hooks not listed above.
