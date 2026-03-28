# User Onboarding + Drift Warning — Pipeline Visibility for New and Returning Users

## Problem

Two visibility gaps affect users who install zie-framework:

1. **New users get no pipeline orientation.** `/zie-init` prints "Next: Run /zie-status"
   but never explains the 6-stage pipeline. Users encounter /zie-backlog, /zie-spec,
   etc. as isolated commands with no mental model of how they connect.

2. **Returning users don't see knowledge drift.** When project structure changes between
   sessions (new dirs, renamed files, deps added), the session-resume hook prints the
   active feature but never warns that the knowledge files may be stale. Users work with
   an outdated project model until someone manually runs `/zie-resync`.

## Motivation

A framework that installs enterprise-standard practices is only valuable if users
understand and follow those practices. Onboarding at init time + automatic drift
detection at session start ensures every user — first-time or returning — knows where
they are and what to do next.

This is low-implementation-effort but high UX leverage: both changes are 5-15 line
additions to existing hooks/commands.

## Rough Scope

**zie-init.md — post-init pipeline summary:**
- After printing the "initialized" confirmation, always print:
  ```
  SDLC pipeline:
    /zie-backlog → /zie-spec → /zie-plan → /zie-implement → /zie-release → /zie-retro
  Each stage has quality gates. Run /zie-status anytime to see where you are.
  First feature: /zie-backlog "your idea here"
  ```
- For existing-project migration: add "Your existing specs/plans have been migrated
  to zie-framework/specs/ and plans/" if migration ran

**hooks/session-resume.py — knowledge drift detection:**
- After printing active feature, run `python3 hooks/knowledge-hash.py --check`:
  computes current hash, compares to stored hash in `.config`
- If drift detected: print `[zie-framework] Knowledge drift detected since last session
  — run /zie-resync to update project context`
- If no `.config` (fresh init): skip check
- Must stay within the outer guard (exit 0 on any exception — never block Claude)

**Tests:**
- zie-init output contains pipeline summary string
- session-resume prints drift warning when hash mismatch
- session-resume is silent when hash matches
- session-resume exits 0 even if knowledge-hash.py crashes
