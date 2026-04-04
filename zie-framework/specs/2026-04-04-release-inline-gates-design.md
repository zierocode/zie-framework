---
slug: release-inline-gates
status: draft
date: 2026-04-04
---
# Spec: Replace Agent-spawned gates in /zie-release with inline Bash tool calls

## Problem

`/zie-release` currently spawns four `Agent()` subagents to run test gates
(integration tests, e2e tests, visual check, and docs-sync-check). Each
subagent invocation adds token overhead, latency, and failure modes with no
real benefit — these gates are simple shell commands (`make test-int`,
`make test-e2e`) or file reads (docs-sync-check). Running them as inline
`Bash` tool calls with `run_in_background=True` achieves identical gate
semantics with zero subagent overhead and eliminates four redundant context
windows per release.

Additional problem: the docs-sync-check (Pre-Gate-1) currently spawns an
Agent to read CLAUDE.md and README.md and compare against the scanned
command/skill/hook files. This check is pure file I/O + string matching —
no reasoning required. It should be done inline as a series of Read/Grep/Bash
calls.

## Proposed Solution

Replace every `Agent(...)` call in `/zie-release` with an equivalent `Bash`
tool call using `run_in_background=True`. Retain all gate logic, conditional
skipping, failure collection, and block-on-failure behaviour exactly as-is.

### Approach C: Parallel Bash tool calls with `run_in_background=True`

#### Pre-Gate-1: Docs Sync — inline Bash

Replace the `Agent(...)` docs-sync-check with a direct inline Bash call:

```bash
# run_in_background=True
python3 -c "
import re, pathlib, json, sys
cmds_dir = pathlib.Path('zie-framework/commands')
skills_dir = pathlib.Path('zie-framework/skills')
hooks_dir = pathlib.Path('hooks')
claude_md = pathlib.Path('CLAUDE.md').read_text()
readme = pathlib.Path('README.md').read_text()
commands = [f.stem for f in cmds_dir.glob('zie-*.md')]
skills = [f.parent.name for f in skills_dir.glob('*/SKILL.md')]
hook_events = re.findall(r'\"event\"\s*:\s*\"([^\"]+)\"', pathlib.Path('hooks/hooks.json').read_text())
missing = [c for c in commands if c not in claude_md]
missing += [s for s in skills if s not in readme]
if missing:
    print('[docs-sync] FAILED:', missing)
    sys.exit(1)
print('[docs-sync] PASSED')
"
```

Result collected with other parallel gates. On `[docs-sync] FAILED` →
update stale docs inline before version bump (no Agent needed — use
Read/Edit/Write directly).

#### Gate 2: Integration tests — inline Bash

```bash
# run_in_background=True
make test-int
```

Report `[Gate 2/5] PASSED`, `[Gate 2/5] SKIPPED` (no integration tests), or
`[Gate 2/5] FAILED: <stderr>`.

#### Gate 3: E2E tests — inline conditional Bash

Read `playwright_enabled` from `zie-framework/.config` inline before
launching. If `playwright_enabled=false` → skip (print `[Gate 3/5] SKIPPED`),
no Bash call. If true:

```bash
# run_in_background=True
make test-e2e
```

#### Gate 4: Visual check — inline conditional Bash

Read `has_frontend` and `playwright_enabled` from `zie-framework/.config`
inline. If `has_frontend=false` or `playwright_enabled=false` → skip (print
`[Gate 4/5] SKIPPED`). If both true:

```bash
# run_in_background=True
make visual-check
```

#### Lint gate — inline Bash

`make lint` currently runs inline as a Bash call — no change required.

#### Failure collection

After all background Bash calls complete, collect all exit codes and
output in a single pass. Report all failures together before halting:

```
[Gate 2/5] FAILED: integration test output here
[Gate 3/5] FAILED: e2e test output here
```

Do NOT halt at first failure. Collect all results, then STOP if any failed.
Gate block-on-failure behaviour is unchanged.

### What does NOT change

- Gate ordering: Pre-Gate-1 → Gate 1 (unit, sequential) → Gates 2–4
  (parallel) → Gate 5 (code diff)
- Conditional skipping: `playwright_enabled` and `has_frontend` checks
  remain, now read inline from `.config` rather than inside an Agent
- Failure semantics: any gate failure halts release before version bump
- Docs-sync failure handling: stale docs still updated before version bump
- Fallback comment removed: no longer needed (Bash is always available)

## Acceptance Criteria

- [ ] AC1: `/zie-release` command file contains zero `Agent(...)` calls for
  gate steps (Pre-Gate-1, Gate 2, Gate 3, Gate 4)
- [ ] AC2: Gates 2, 3, and 4 are issued as `Bash` tool calls with
  `run_in_background=True` (denoted clearly in the command prose/pseudocode)
- [ ] AC3: Pre-Gate-1 docs-sync-check is issued as an inline `Bash` tool call
  (no `Agent()`, no subagent spawn), reading CLAUDE.md and README.md directly
- [ ] AC4: Conditional gates (Gate 3 e2e, Gate 4 visual) still skip when
  `playwright_enabled=false` — skip decision made inline before the Bash call
  is issued; the Bash call is never spawned if the condition is false
- [ ] AC5: Failure collection collects all gate exit codes before halting —
  no early-exit after first failure; all failures printed together
- [ ] AC6: Gate block-on-failure behaviour is unchanged — release does not
  proceed to version bump if any gate fails
- [ ] AC7: Token overhead for gates drops to approximately zero (no Agent
  context windows spawned for gate execution)

## Out of Scope

- Changing gate commands themselves (`make test-int`, `make test-e2e`, etc.)
- Adding new gates
- Changing Gate 1 (unit tests) — already runs inline as a sequential Bash call
- Changing Gate 5 (code diff) — already inline
- Changes to any hook, Makefile target, or test file
- Unit tests for this change — the command file is Markdown prose; AC
  verified by reading the updated `commands/zie-release.md` and confirming
  the absence of `Agent(` calls for gate steps

## Test Plan

No unit tests applicable (command file is Markdown, not executable code).
Verification:

1. Read `commands/zie-release.md` after implementation.
2. Grep for `Agent(` in the gate sections — must return zero matches for
   Pre-Gate-1, Gate 2, Gate 3, Gate 4.
3. Grep for `run_in_background=True` — must appear for each of the three
   parallel gate Bash calls.
4. Confirm conditional skip logic for Gate 3 and Gate 4 precedes the Bash
   call (not inside an Agent prompt string).
