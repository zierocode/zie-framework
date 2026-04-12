# Backlog: Trim CLAUDE.md to trigger-table format (<80 lines)

**Problem:**
CLAUDE.md is ~160 lines / ~7KB and is loaded on every prompt turn (prompt-cached
but still counts toward context window). The "Hook Output Convention", "Hook Error
Handling Convention", "Hook Context Hints", and config key table are read by Claude
on every turn but are only useful when writing new hooks — which happens rarely.

**Motivation:**
External research confirms a real-world 54% token reduction by replacing
documentation paragraphs with trigger tables (johnlindquist gist). At ~500–800 tokens
saved per turn, a 50-turn session wastes 25,000–40,000 tokens on static prose that
Claude never acts on.

**Rough scope:**
- Move "Hook Output Convention", "Hook Error Handling Convention", "Hook Context Hints"
  sections to `zie-framework/project/hook-conventions.md`
- Move optional-dependency config key table to `zie-framework/project/config-reference.md`
- CLAUDE.md keeps: project overview, stack, commands table, key rules, dev commands
- Target: under 80 lines
- Update /resync and /init templates to reference the new project docs
- Tests: verify CLAUDE.md line count in docs-sync-check or a lint rule
