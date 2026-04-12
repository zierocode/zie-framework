---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-stop-guard-nudge-per-stop.md
---

# Lean Stop-Guard Nudge Per Stop — Implementation Plan

**Goal:** Gate `_run_nudges()` in `stop-guard.py` behind a 30-min session-scoped TTL, replace the O(history) `git log --all -p` with a lightweight format, and add `shlex.quote(slug)` for shell injection safety.

**Architecture:** The existing `get_cached_git_status`/`write_git_status_cache` infrastructure in `utils_roadmap.py` is reused with key `"nudge-check"` and TTL=1800s. No new utility functions needed. The TTL gate is inserted in the inner-operations block of `stop-guard.py` immediately before the `_run_nudges()` call. The git log format change and `shlex.quote` are surgical replacements inside `_run_nudges()`.

**Tech Stack:** Python 3.x, subprocess, shlex, existing utils_roadmap cache helpers.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/stop-guard.py` | Add TTL gate, replace git log format, add shlex.quote |
| Modify | `tests/unit/test_nudges_stop_guard.py` | Add TTL gate tests (cache hit skips, cache miss runs) |
| Modify | `tests/unit/test_stop_guard.py` | Add source-invariant tests for shlex.quote and new git format |

---

## Task 1: Replace `git log --all -p` with lightweight format + add `shlex.quote`

**Acceptance Criteria:**
- `_run_nudges()` uses `git log --all --format="%H %ai"` instead of `git log --all -p`
- The grep argument wrapping the slug uses `shlex.quote(slug)` inside the shell command string
- `shlex` is imported at the top of `stop-guard.py`
- Existing nudge behaviour (date extraction, nudge message) is unchanged

**Files:**
- Modify: `hooks/stop-guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_stop_guard.py` in `TestSourceInvariants`:

  ```python
  def test_uses_lightweight_git_log_format(self):
      """stop-guard.py must NOT use git log --all -p (patch body)."""
      source = Path(HOOK).read_text()
      assert "git log --all -p" not in source, (
          "Use git log --all --format='%H %ai' instead of git log --all -p"
      )

  def test_uses_shlex_quote_for_slug(self):
      """stop-guard.py must use shlex.quote(slug) in the grep argument."""
      source = Path(HOOK).read_text()
      assert "shlex.quote" in source, (
          "slug must be shlex-quoted before shell injection"
      )
  ```

  Run: `make test-unit` — must FAIL (current source uses `git log --all -p`, no shlex.quote)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/stop-guard.py`, add `import shlex` at the top-level imports block (after `import sys`).

  Inside `_run_nudges()`, replace the Nudge 1 subprocess block:

  ```python
  # BEFORE:
  result = subprocess.run(
      f"git log --all -p -- zie-framework/ROADMAP.md "
      f"| grep -B5 '+- \\[ \\] {slug}'",
      cwd=str(cwd),
      capture_output=True,
      text=True,
      timeout=subprocess_timeout,
      shell=True,  # nosec B602 — piped git log | grep, slug from ROADMAP (internal)
  )
  if result.returncode == 0 and result.stdout.strip():
      date_match = _re.search(r'^Date:\s+(\d{4}-\d{2}-\d{2})', result.stdout, _re.MULTILINE)
      if not date_match:
          date_match = _re.search(r'(\d{4}-\d{2}-\d{2})', result.stdout)
  ```

  ```python
  # AFTER:
  result = subprocess.run(
      f"git log --all --format='%H %ai' -- zie-framework/ROADMAP.md "
      f"| grep {shlex.quote(slug)}",
      cwd=str(cwd),
      capture_output=True,
      text=True,
      timeout=subprocess_timeout,
      shell=True,  # nosec B602 — piped git log | grep, slug shlex-quoted
  )
  if result.returncode == 0 and result.stdout.strip():
      date_match = _re.search(r'(\d{4}-\d{2}-\d{2})', result.stdout)
  ```

  Note: The `%ai` format outputs ISO 8601 datetime (e.g. `2026-04-04 12:00:00 +0700`), so the existing bare `(\d{4}-\d{2}-\d{2})` regex still extracts the date correctly. The `^Date:\s+` branch is removed since it no longer applies.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the now-dead `date_match = _re.search(r'^Date:\s+...` branch entirely if it was previously kept as a fallback — Task 1 Step 2 already removes it. Verify the `nosec` annotation is updated to reflect `shlex.quote` usage. Run: `make test-unit` — still PASS

---

## Task 2: Add TTL gate around `_run_nudges()` call

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- On Stop event N (same session, within 30 min): `_run_nudges()` is NOT called when TTL sentinel exists
- On Stop event 1 (cache miss): TTL sentinel is written, then `_run_nudges()` is called
- When `CLAUDE_SESSION_ID` is absent, nudges run every stop (degenerate case, no regression)
- `_run_nudges()` is never skipped when a block would also be emitted (block check is unaffected)

**Files:**
- Modify: `hooks/stop-guard.py`
- Modify: `tests/unit/test_nudges_stop_guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add new test class to `tests/unit/test_nudges_stop_guard.py`:

  ```python
  class TestNudgeTTLGate:
      def test_nudge_skipped_on_cache_hit(self, tmp_path):
          """When nudge-check sentinel is fresh, nudges do not run."""
          import time, uuid
          session_id = str(uuid.uuid4())
          # Write a fresh sentinel (age < 1800s)
          from utils_roadmap import write_git_status_cache
          import sys, os
          sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
          write_git_status_cache(session_id, "nudge-check", "1")
          # Set up a stale backlog item that would normally fire nudge 3
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n"
              "## Next\n"
              "- [ ] old-item — 2019-01-01\n\n"
              "## Done\n"
          )
          env = {
              **os.environ,
              "CLAUDE_CWD": str(tmp_path),
              "CLAUDE_SESSION_ID": session_id,
          }
          r = subprocess.run(
              [sys.executable, HOOK],
              input=json.dumps({}),
              capture_output=True, text=True, env=env,
          )
          assert r.returncode == 0
          assert "[zie-framework] nudge:" not in r.stdout

      def test_nudge_runs_on_cache_miss(self, tmp_path):
          """When nudge-check sentinel is absent, nudges run normally."""
          import uuid
          session_id = str(uuid.uuid4())
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n"
              "## Next\n"
              "- [ ] old-item — 2019-01-01\n\n"
              "## Done\n"
          )
          env = {
              **os.environ,
              "CLAUDE_CWD": str(tmp_path),
              "CLAUDE_SESSION_ID": session_id,
          }
          r = subprocess.run(
              [sys.executable, HOOK],
              input=json.dumps({}),
              capture_output=True, text=True, env=env,
          )
          assert r.returncode == 0
          assert "[zie-framework] nudge:" in r.stdout
          assert "30 days" in r.stdout

      def test_nudge_runs_when_no_session_id(self, tmp_path):
          """When CLAUDE_SESSION_ID is unset, nudges run (degenerate: no caching)."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n"
              "## Next\n"
              "- [ ] old-item — 2019-01-01\n\n"
              "## Done\n"
          )
          env = {k: v for k, v in os.environ.items() if k != "CLAUDE_SESSION_ID"}
          env["CLAUDE_CWD"] = str(tmp_path)
          r = subprocess.run(
              [sys.executable, HOOK],
              input=json.dumps({}),
              capture_output=True, text=True, env=env,
          )
          assert r.returncode == 0
          # nudges still fire (no session = no TTL caching)
          assert "[zie-framework] nudge:" in r.stdout
  ```

  Run: `make test-unit` — must FAIL (no TTL gate yet)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/stop-guard.py`, in the inner-operations block, replace the existing `_run_nudges()` call site:

  ```python
  # BEFORE (at end of inner-operations block):
  # --- Proactive nudges ---
  _run_nudges(cwd, config, subprocess_timeout)
  sys.exit(0)
  ```

  ```python
  # AFTER:
  # --- Proactive nudges (session-scoped TTL gate — 30 min) ---
  _nudge_cached = get_cached_git_status(session_id, "nudge-check", ttl=1800)
  if _nudge_cached is None:
      write_git_status_cache(session_id, "nudge-check", "1")
      _run_nudges(cwd, config, subprocess_timeout)
  sys.exit(0)
  ```

  `session_id` is already assigned earlier in the block (`session_id = os.environ.get("CLAUDE_SESSION_ID", "")`), so no additional variable is needed.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the TTL gate does not interfere with the block path: the block check (`if uncommitted:`) exits before reaching the nudge gate, so nudges are never gated when a block is emitted — correct by structure. Add a comment clarifying this ordering. Run: `make test-unit` — still PASS

---

## Task 3: Source-invariant tests for TTL gate wiring

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `test_stop_guard.py` source-invariants verify `get_cached_git_status` and `write_git_status_cache` are used for the nudge gate
- Test verifies TTL value is 1800 (30 min)

**Files:**
- Modify: `tests/unit/test_stop_guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `TestSourceInvariants` in `tests/unit/test_stop_guard.py`:

  ```python
  def test_nudge_gate_uses_cache_helpers(self):
      """stop-guard.py must use get_cached_git_status for the nudge TTL gate."""
      source = Path(HOOK).read_text()
      assert 'get_cached_git_status' in source
      assert 'write_git_status_cache' in source

  def test_nudge_gate_ttl_is_1800(self):
      """Nudge TTL must be 1800 seconds (30 min)."""
      source = Path(HOOK).read_text()
      assert 'ttl=1800' in source, "Nudge gate TTL must be hardcoded to 1800s"

  def test_nudge_gate_key_is_nudge_check(self):
      """Nudge gate cache key must be 'nudge-check'."""
      source = Path(HOOK).read_text()
      assert '"nudge-check"' in source, "Cache key must be 'nudge-check'"
  ```

  Run: `make test-unit` — must FAIL (before Task 2 is done; if run after Task 2, will PASS)

  Note: These tests are written after Tasks 1+2 are complete, so they will PASS immediately. The RED phase is validated structurally — these are regression guards.

- [ ] **Step 2: Implement (GREEN)**

  No code changes — tests pass after Tasks 1 and 2.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review full `stop-guard.py` for any residual `git log --all -p` references or unquoted slug usage. Run `make lint`. Run: `make test-unit` — still PASS

---

## Completion Gate

```bash
make test-unit   # all unit tests green
make lint        # no lint errors
```

Expected: all 3 tasks complete, no regressions in `test_stop_guard.py` or `test_nudges_stop_guard.py`.
