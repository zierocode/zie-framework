---
approved: false
approved_at:
backlog: backlog/intent-sdlc-early-exit.md
spec: specs/2026-04-04-intent-sdlc-early-exit-design.md
---

# Intent SDLC — Length + Keyword Early-Exit Guard — Implementation Plan

**Goal:** Add two sequential early-exit gates at the top of the inner block in `hooks/intent-sdlc.py` so that trivially short messages and messages containing no SDLC keywords never reach `read_roadmap_cached()`.

**Architecture:** Two `sys.exit(0)` guards inserted immediately after `session_id` assignment in the existing inner `try` block — Gate 1 rejects messages with `len(message.strip()) < 15`, Gate 2 rejects messages that match zero entries in the already-compiled `COMPILED_PATTERNS` dict. No new module-level symbols, no new config keys, no changes to detection logic or outer guard.

**Tech Stack:** Python 3.x (hooks/intent-sdlc.py), pytest (tests/unit/test_intent_sdlc_early_exit.py)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/intent-sdlc.py` | Insert Gate 1 (length) + Gate 2 (keyword) at top of inner try block |
| Create | `tests/unit/test_intent_sdlc_early_exit.py` | TDD tests for both gates (written RED first) |

---

## Task 1: Write failing tests for both early-exit gates (RED)

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/unit/test_intent_sdlc_early_exit.py` exists with `TestLengthGate` and `TestKeywordGate` classes
- Running `make test-unit` shows all new tests FAILING (hook has not been modified yet)
- No existing tests are broken

**Files:**
- Create: `tests/unit/test_intent_sdlc_early_exit.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_intent_sdlc_early_exit.py
  """Tests for length + keyword early-exit gates in hooks/intent-sdlc.py."""
  import json
  import os
  import subprocess
  import sys

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


  def run_hook(prompt: str, tmp_cwd=None, session_id: str = "test-early-exit") -> subprocess.CompletedProcess:
      hook = os.path.join(REPO_ROOT, "hooks", "intent-sdlc.py")
      env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
      if tmp_cwd:
          env["CLAUDE_CWD"] = str(tmp_cwd)
      event = {"session_id": session_id, "prompt": prompt}
      return subprocess.run(
          [sys.executable, hook],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          env=env,
      )


  def make_cwd_with_zf(tmp_path, roadmap_content: str = "## Now\n\n## Next\n"):
      (tmp_path / "zie-framework").mkdir(parents=True)
      (tmp_path / "zie-framework" / "ROADMAP.md").write_text(roadmap_content)
      return tmp_path


  class TestLengthGate:
      """Gate 1: messages with len(message.strip()) < 15 must exit silently."""

      def test_empty_string_exits(self, tmp_path):
          # Caught by outer guard (len < 3) — stdout must be empty
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("", tmp_cwd=cwd, session_id="test-lg-empty")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_two_char_exits(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("ok", tmp_cwd=cwd, session_id="test-lg-ok")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_14_char_exits(self, tmp_path):
          # "implement this" = 14 chars — must exit silently
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("implement this", tmp_cwd=cwd, session_id="test-lg-14")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_15_char_passes(self, tmp_path):
          # "implement this!" = 15 chars, has SDLC keyword — must produce output
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("implement this!", tmp_cwd=cwd, session_id="test-lg-15")
          assert r.returncode == 0
          assert r.stdout.strip() != ""

      def test_borderline_with_spaces_exits(self, tmp_path):
          # "  ok  " strips to "ok" (2 chars) — must exit silently
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("  ok  ", tmp_cwd=cwd, session_id="test-lg-spaces")
          assert r.returncode == 0
          assert r.stdout.strip() == ""


  class TestKeywordGate:
      """Gate 2: messages >= 15 chars with no SDLC keyword must exit silently."""

      def test_no_keyword_long_message_exits(self, tmp_path):
          # 36 chars, no SDLC keyword
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("what is the weather today over there", tmp_cwd=cwd, session_id="test-kg-weather")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_url_only_exits(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("https://example.com/some/path/here", tmp_cwd=cwd, session_id="test-kg-url")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_generic_question_exits(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("can you explain how async works here", tmp_cwd=cwd, session_id="test-kg-async")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_fix_keyword_passes(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("there is a bug in the auth module", tmp_cwd=cwd, session_id="test-kg-fix")
          assert r.returncode == 0
          assert r.stdout.strip() != ""

      def test_implement_keyword_passes(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("let us implement this feature now", tmp_cwd=cwd, session_id="test-kg-impl")
          assert r.returncode == 0
          assert r.stdout.strip() != ""

      def test_plan_keyword_passes(self, tmp_path):
          cwd = make_cwd_with_zf(tmp_path)
          r = run_hook("we should plan this backlog item", tmp_cwd=cwd, session_id="test-kg-plan")
          assert r.returncode == 0
          assert r.stdout.strip() != ""
  ```

  Run: `make test-unit` — new tests in `TestLengthGate` and `TestKeywordGate` must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  No implementation in this task — implementation is in Task 2.

- [ ] **Step 3: Refactor**

  N/A — test file only.

---

## Task 2: Add Gate 1 (length) and Gate 2 (keyword) to hooks/intent-sdlc.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Gate 1: `if len(message.strip()) < 15: sys.exit(0)` is the first statement inside the inner `try` block after `session_id = event.get(...)`
- Gate 2: `has_sdlc_keyword` uses `COMPILED_PATTERNS` directly — no new regex compilation
- Both gates are inside the inner `try` block, not the outer guard
- All new tests in `TestLengthGate` and `TestKeywordGate` pass
- All existing tests in `test_hooks_intent_sdlc.py` continue to pass

**Files:**
- Modify: `hooks/intent-sdlc.py`

- [ ] **Step 1: Write failing tests (RED)**

  Already written in Task 1. Confirm they still fail before editing:
  Run: `make test-unit` — `TestLengthGate` + `TestKeywordGate` must **FAIL**

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/intent-sdlc.py`, locate the inner `try` block. The current opening is:

  ```python
  try:
      session_id = event.get("session_id", "default")

      # ── Intent detection (no ROADMAP needed) ─────────────────────────────────
  ```

  Replace with:

  ```python
  try:
      session_id = event.get("session_id", "default")

      # ── Early-exit guards ─────────────────────────────────────────────────────
      if len(message.strip()) < 15:
          sys.exit(0)

      has_sdlc_keyword = any(
          p.search(message)
          for compiled_pats in COMPILED_PATTERNS.values()
          for p in compiled_pats
      )
      if not has_sdlc_keyword:
          sys.exit(0)

      # ── Intent detection (no ROADMAP needed) ─────────────────────────────────
  ```

  Run: `make test-unit` — all tests must **PASS**

- [ ] **Step 3: Refactor**

  - Verify the comment header `# ── Early-exit guards` aligns with existing comment style in the file
  - Confirm `has_sdlc_keyword` is not referenced anywhere else (local variable only)
  - Run: `make lint` — must pass with no violations
  - Run: `make test-unit` — still PASS

---

## Task 3: Regression — full suite

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- AC-4: All existing tests in `test_hooks_intent_sdlc.py` pass
- AC-5: `test_intent_sdlc_regex.py` AST check passes (no new regex compilation introduced)
- `make test-ci` exits 0

**Files:**
- No file changes

- [ ] **Step 1: Write failing tests (RED)**

  N/A — regression uses existing tests only.

- [ ] **Step 2: Implement (GREEN)**

  Run: `make test-ci`

  Expected output includes:
  ```
  tests/unit/test_hooks_intent_sdlc.py  PASSED (all classes)
  tests/unit/test_intent_sdlc_regex.py  PASSED
  tests/unit/test_intent_sdlc_early_exit.py  PASSED (11 tests)
  ```

- [ ] **Step 3: Refactor**

  N/A.
