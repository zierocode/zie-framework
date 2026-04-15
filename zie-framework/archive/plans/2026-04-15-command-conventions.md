---
date: 2026-04-15
status: approved
slug: command-conventions
---

# Implementation Plan: command-conventions

## Steps

### Task 1: Expand command-conventions.md

Add two new sections to `zie-framework/project/command-conventions.md`:

- **Error format**: `STOP: <action-oriented message>` for blockers, `⚠ <message>` for warnings, `ℹ️ <advice>` for tips. No emojis in STOP/⚠ lines.
- **Output format**: Every command prints (1) header line: `/command — <one-line description>`, (2) body: structured content, (3) footer: `→ /next-command` suggestion.
- **Pre-flight opt-out**: Commands that are read-only or don't need ROADMAP (`/health`, `/brief`, `/guide`) mark `preflight: minimal` (existence check only). All others use `preflight: full`.

Keep existing Pre-flight section unchanged.

### Task 2: Normalize pre-flight guards across commands

For each command with `preflight: full`:
- Ensure step 1 checks `zie-framework/` existence → `STOP: Run /init first.`
- Ensure step 2 reads `.config` before using any config value
- Ensure step 3 reads ROADMAP and applies WIP guard where appropriate
- Remove inline duplicate checks; replace with `See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).`

For `preflight: minimal` commands: keep only existence check.

### Task 3: Normalize error messages

Grep all commands for inconsistent error patterns (`❌`, `Error:`, `Failed to`, bare stops). Replace with convention format. Verify no behavior change — only message wording.

### Task 4: Normalize output format

Add header line and footer to commands missing them. Ensure tables use consistent `| | |` markdown format. Remove trailing summaries — next-step footer replaces them.

## Tests

- `test_command_conventions.py`: parse all 20 command files, assert each has a pre-flight reference or opt-out, assert error messages match convention regex, assert header/footer present
- `test_preflight_guards.py`: for each `preflight: full` command, verify the 3 guard steps appear in order

## Acceptance Criteria

- All 20 command files reference `command-conventions.md` or declare `preflight: minimal`
- Zero error messages deviate from `STOP:` / `⚠` / `ℹ️` format
- Every command has header line and next-step footer
- Tests pass: `make test-unit`