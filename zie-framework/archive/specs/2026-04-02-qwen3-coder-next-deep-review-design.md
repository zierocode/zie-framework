---
approved: true
approved_at: 2026-04-02
backlog: backlog/qwen3-coder-next-deep-review.md
spec: specs/2026-04-02-qwen3-coder-next-deep-review-design.md
---

# Spec: Qwen3-coder-next Deep Review — Hook & Compatibility Fixes

**Status:** APPROVED  
**Date:** 2026-04-02  
**approved:** true

---

## Problem

Deep review of zie-framework identified 10 compatibility issues when used with the `qwen3-coder-next:cloud` model. These range from critical bugs that block execution to code quality improvements.

---

## Motivation

Zie runs Claude with `qwen3-coder-next:cloud` model. The framework was designed and tested primarily with Claude models. This review identifies compatibility issues that cause errors or unexpected behavior.

---

## Rough Scope

**Critical fixes (P1 - must fix before using with Qwen):**
- hooks.json syntax errors (`async: true` is invalid)
- safety_check_agent.py assumes `claude` CLI exists
- symlink handling in session-resume.py

**High priority (P2 - fix before production):**
- knowledge-hash.py EXCLUDE_PATHS logic bug
- intent-sdlc.py missing case-insensitive matching
- sdlc-permissions.py incomplete metachar guard

**Low priority (P3 - optional improvements):**
- auto-test.py timeout calculation confusion
- session-cleanup.py glob filtering
- adr_summary.py error handling

---

## Acceptance Criteria

| ID | Requirement | Test |
|----|-------------|------|
| AC1 | Fix `async: true` → `background: true` in hooks.json | tests/hooks/test_hooks.py |
| AC2 | Add CLI check + fallback in safety_check_agent.py | tests/hooks/test_safety_check_agent.py |
| AC3 | Fix symlink handling in session-resume.py | tests/hooks/test_session_resume.py |
| AC4 | Fix EXCLUDE_PATHS logic in knowledge-hash.py | tests/hooks/test_knowledge_hash.py |
| AC5 | Add IGNORECASE to intent-sdlc.py patterns | tests/hooks/test_intent_sdlc.py |
| AC6 | Expand metachar guard in sdlc-permissions.py | tests/hooks/test_sdlc_permissions.py |
| AC7 | Clarify timeout logic in auto-test.py | tests/hooks/test_auto_test.py |
| AC8 | Filter files in session-cleanup.py | tests/hooks/test_session_cleanup.py |
| AC9 | Add fallback in adr_summary.py | tests/hooks/test_adr_summary.py |

---

## Design

See `/zie-plan` for detailed implementation tasks.

---

## Dependencies

- None (standalone fix)

---

## Notes

- All fixes must be non-breaking for existing Claude model users
- Each fix should have unit tests
- Documentation updates in CLAUDE.md and README.md
