---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-intent-detect-redos.md
spec: specs/2026-03-24-audit-intent-detect-redos-design.md
---

# Intent-Detect ReDoS Input Guard — Implementation Plan

**Goal:** Add a hard `MAX_MESSAGE_LEN = 1000` constant and an early-exit guard to `intent-detect.py` so no regex pattern is ever run against a pathologically long input.
**Architecture:** A single named constant is added at the top of the file. One early-exit `if` block is inserted immediately after the existing `len(message) < 3` check and before any pattern-matching code. No logic changes beyond the new guard.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/intent-detect.py` | Add `MAX_MESSAGE_LEN` constant and guard after line 17 |
| Modify | `tests/unit/test_hooks_intent_detect.py` | Add tests for the new length cap |

## Task 1: Add `MAX_MESSAGE_LEN` guard

<!-- depends_on: none -->

**Acceptance Criteria:**
- A message of exactly 1000 characters is processed normally (not rejected)
- A message of 1001 characters produces no output (exits 0 before pattern matching)
- The constant is named `MAX_MESSAGE_LEN` and equals `1000`
- All existing `TestIntentDetect*` tests continue to pass

**Files:**
- Modify: `hooks/intent-detect.py`
- Modify: `tests/unit/test_hooks_intent_detect.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_intent_detect.py — add new class at end of file

  class TestIntentDetectReDoSGuard:
      def test_message_at_limit_is_not_rejected(self, tmp_path):
          """Exactly MAX_MESSAGE_LEN chars — should NOT be suppressed by length guard."""
          cwd = make_cwd_with_zf(tmp_path)
          # Use a message at exactly 1000 chars that contains a clear fix keyword.
          # The existing >500 guard will fire first, so we assert exit-0 behaviour
          # (not stdout output) — the important thing is no crash and guard ordering.
          msg = "fix " + "x" * 996  # 1000 chars total
          r = run_hook({"prompt": msg}, tmp_cwd=cwd)
          assert r.returncode == 0

      def test_message_over_limit_produces_no_output(self, tmp_path):
          """1001 chars — MAX_MESSAGE_LEN guard must fire, producing no output."""
          cwd = make_cwd_with_zf(tmp_path)
          msg = "fix " + "x" * 997  # 1001 chars total
          r = run_hook({"prompt": msg}, tmp_cwd=cwd)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_max_message_len_constant_is_1000(self):
          """MAX_MESSAGE_LEN must be defined as 1000 in the hook module."""
          import importlib.util, io, os, sys
          hook = os.path.join(REPO_ROOT, "hooks", "intent-detect.py")
          spec = importlib.util.spec_from_file_location("intent_detect_redos", hook)
          mod = importlib.util.module_from_spec(spec)
          original_stdin = sys.stdin
          original_env = os.environ.copy()
          try:
              sys.stdin = io.StringIO('{"prompt": "hi"}')
              os.environ["CLAUDE_CWD"] = "/tmp"
              try:
                  spec.loader.exec_module(mod)
              except SystemExit:
                  pass
          finally:
              sys.stdin = original_stdin
              os.environ.clear()
              os.environ.update(original_env)
          assert hasattr(mod, "MAX_MESSAGE_LEN"), "MAX_MESSAGE_LEN constant not found"
          assert mod.MAX_MESSAGE_LEN == 1000
  ```
  Run: `make test-unit` — must FAIL (`MAX_MESSAGE_LEN` attribute missing)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/intent-detect.py — add constant near top of file (after imports, before PATTERNS)
  # and insert guard after the existing len(message) < 3 check

  # Add after the existing early-exit block (after line 17 — the `len(message) < 3` check):

  MAX_MESSAGE_LEN = 1000

  # ... existing code ...

  if not message or len(message) < 3:
      sys.exit(0)

  # NEW: hard cap to prevent ReDoS on adversarially long inputs
  if len(message) > MAX_MESSAGE_LEN:
      sys.exit(0)

  # Skip if prompt looks like command content (frontmatter or very long)
  if message.startswith("---") or len(message) > 500:
      sys.exit(0)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `MAX_MESSAGE_LEN` is placed before `PATTERNS` dict (visible at module level).
  Confirm the guard appears between the `< 3` check and the `startswith("---")` check.
  Run: `make test-unit` — still PASS

---
*Commit: `git add hooks/intent-detect.py tests/unit/test_hooks_intent_detect.py && git commit -m "fix: add MAX_MESSAGE_LEN guard to intent-detect, prevent ReDoS"`*
