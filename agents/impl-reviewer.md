---
description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
background: true
allowed-tools: Read, Glob, Grep, Bash
---

# impl-reviewer agent

Invoke `Skill(zie-framework:impl-reviewer)` with the task description, Acceptance
Criteria, and list of files changed provided by the caller.

## Bash tool scope

The `Bash` tool is permitted exclusively for `make test*` commands — to verify
the test suite state as part of the Phase 2 AC coverage check. No other shell
commands are needed.
