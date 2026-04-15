---
date: 2026-04-15
status: approved
slug: command-conventions
---

# Normalize Command Conventions

## Problem

Commands have inconsistent pre-flight guards, error messages, and output formats. `/implement` has full pre-flight with WIP guards; `/audit` has none. Error prefixes vary (`STOP:`, `❌`, plain text). Output structure differs across commands — some use tables, some use prose, some have headers, some don't. The existing `command-conventions.md` only covers 3 pre-flight steps and no formatting rules.

## Solution

Expand `command-conventions.md` into the single source of truth for command protocol, then bring all 20 commands into compliance. Define 3 sections: **Pre-flight** (existence check, config load, ROADMAP read, WIP guard — with opt-out per command), **Error format** (`STOP: <action>` for blocking, `⚠ <message>` for warnings, `ℹ️ <tip>` for advisories), **Output format** (header line, body, next-step footer). Commands reference the doc instead of duplicating checks inline.

## Rough Scope

- Expand `zie-framework/project/command-conventions.md` with error format and output format sections
- Audit all 20 commands; normalize pre-flight guards, error messages, and output structure
- No behavior or workflow changes — purely structural consistency

## Files Changed

- `zie-framework/project/command-conventions.md` — expanded with error + output conventions
- `commands/*.md` — all 20 command files normalized