---
tags: [chore]
---

# Normalize Command Conventions

## Problem

Commands don't follow consistent conventions for pre-flight checks, error messages, or output formatting. Some have ad-hoc patterns, others follow the established `command-conventions.md` template partially.

## Rough Scope

**In:**
- Audit all commands against `command-conventions.md`
- Add missing pre-flight guards (context bundle loading, config read, ROADMAP existence check)
- Normalize error messages (consistent prefix format, action-oriented wording)
- Ensure consistent output format (header, body, footer sections)

**Out:**
- Changing command behavior or workflow steps
- Changing command names or file paths

## Priority

MEDIUM