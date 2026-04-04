# Backlog: Collapse /audit command and zie-audit skill into one canonical pipeline

**Problem:**
commands/audit.md has its own 4-phase pipeline with 4 parallel agents (Security/Deps,
Code Health/Perf, Structural/Obs, External Research). skills/zie-audit/SKILL.md has
an overlapping but different 5-phase pipeline with 5 agents (Security, Lean/Efficiency,
Quality, Docs, Architecture). They duplicate Phase 1 context bundle logic, ADR cache
writes, and synthesis. CLAUDE.md says /audit invokes Skill(zie-framework:zie-audit),
but the command itself already contains a standalone audit — the skill then re-reads
.config and PROJECT.md on top.

**Motivation:**
~3,000–5,000 tokens of duplicated pipeline logic. Every audit invocation loads both.
One should be the canonical implementation; the other should be a thin dispatcher
(3–5 lines) that delegates entirely to the canonical one.

**Rough scope:**
- Decide canonical location: skill (zie-audit/SKILL.md) is preferred (lazy-loaded)
- Reduce commands/audit.md to a thin dispatcher: frontmatter + `Invoke Skill(zie-framework:zie-audit)`
- Merge any unique agent types from audit.md into zie-audit/SKILL.md (the lean/efficiency
  agent from this session is not in the current skill)
- Ensure `--focus` argument is passed through from command to skill
- Tests: structural test verifying audit.md is under N lines (thin dispatcher threshold)
