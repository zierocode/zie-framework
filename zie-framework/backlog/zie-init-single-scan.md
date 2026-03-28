# zie-init Single-Pass Scan — Eliminate Duplicate Agent Exploration

## Problem

`/zie-init` for existing projects invokes an Explore agent that:
1. Reads README, CHANGELOG, ARCHITECTURE, docs/** as primary sources
2. Scans every file in the codebase for architecture patterns

Then, separately at step 2h, detects "migratable documentation" by rescanning
the same root directories for `**/specs/*.md`, `**/plans/*.md`, `**/decisions/*.md`.
This is two passes over the same directory tree.

For large codebases (1,000+ files), the second scan adds meaningful latency and
doubles the Explore agent's filesystem I/O with no additional information gain.

## Motivation

`/zie-init` runs exactly once per project, so latency isn't critical — but the
double-scan pattern violates the principle of doing things once. More importantly,
the Explore agent's report from pass 1 already includes enough information to detect
migratable docs if the agent prompt asks for it. The second scan exists because the
first prompt didn't ask the right question.

## Rough Scope

**zie-init.md — unify Explore agent prompt:**
- Expand the existing Explore agent invocation to include migration detection in
  its output: "Additionally, list all files matching `**/specs/*.md`, `**/plans/*.md`,
  `**/decisions/*.md`, `**/backlog/*.md` — these are candidates for migration."
- Parse migration candidates from the single agent report
- Remove the separate step 2h directory rescan

**Expected output format addition to Explore agent:**
```json
{
  "architecture": "...",
  "tech_stack": "...",
  "migratable_docs": {
    "specs": ["path/to/spec.md"],
    "plans": [],
    "decisions": ["docs/adr-001.md"]
  }
}
```

**Tests:**
- Explore agent prompt includes migration detection request
- zie-init uses migratable_docs from agent report, no second scan
- Migration step correctly processes agent-reported paths
- Existing init behavior unchanged (functional parity)
