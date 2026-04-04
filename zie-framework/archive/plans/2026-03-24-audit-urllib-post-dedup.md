---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-urllib-post-dedup.md
spec: specs/2026-03-24-audit-urllib-post-dedup-design.md
---

# Shared urllib POST Helper for zie-memory API — Implementation Plan

**Goal:** Extract `call_zie_memory_api(url, key, endpoint, payload, timeout)` into `utils.py` and replace the duplicated inline `urllib.request` blocks in `session-learn.py` and `wip-checkpoint.py`.
**Architecture:** The helper encodes `payload` as JSON, constructs the full URL from `url + endpoint`, sets `Authorization: Bearer` and `Content-Type: application/json` headers, calls `urlopen` with the given timeout, and re-raises on any exception. Each caller retains its own `try/except Exception as e: print(...)` block so error-handling policy is not centralised.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `call_zie_memory_api()` helper |
| Modify | `hooks/session-learn.py` | Replace inline urllib block with `call_zie_memory_api()` call |
| Modify | `hooks/wip-checkpoint.py` | Replace inline urllib block with `call_zie_memory_api()` call |
| Modify | `tests/unit/test_utils.py` | Add unit tests for `call_zie_memory_api()` |
| Modify | `tests/unit/test_hooks_session_learn.py` | Confirm existing tests still pass |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Confirm existing tests still pass |

## Task 1: Add `call_zie_memory_api` helper to `utils.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `call_zie_memory_api(url, key, endpoint, payload, timeout=5)` constructs the request correctly
- It raises `urllib.error.URLError` when the server is unreachable (not swallowed)
- It raises `TypeError` when `payload` contains non-serializable values
- Endpoint is joined as `f"{url}{endpoint}"` (no double-slash normalisation)

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_utils.py — add new class after existing tests

  import urllib.error
  from unittest.mock import patch, MagicMock

  class TestCallZieMemoryApi:
      def test_raises_on_unreachable_url(self):
          from utils import call_zie_memory_api
          with pytest.raises(Exception):
              call_zie_memory_api(
                  "https://localhost:19999",
                  "fake-key",
                  "/api/hooks/session-stop",
                  {"project": "test"},
                  timeout=1,
              )

      def test_raises_type_error_on_non_serializable_payload(self):
          from utils import call_zie_memory_api
          with pytest.raises(TypeError):
              call_zie_memory_api(
                  "https://localhost:19999",
                  "fake-key",
                  "/api/hooks/session-stop",
                  {"bad": object()},
              )

      def test_constructs_correct_request(self):
          from utils import call_zie_memory_api
          captured = {}
          def fake_urlopen(req, timeout):
              captured["url"] = req.full_url
              captured["method"] = req.method
              captured["auth"] = req.get_header("Authorization")
              captured["ct"] = req.get_header("Content-type")
              return MagicMock()
          with patch("utils.urllib.request.urlopen", side_effect=fake_urlopen):
              call_zie_memory_api(
                  "https://api.example.com",
                  "mykey",
                  "/api/hooks/session-stop",
                  {"project": "foo"},
                  timeout=5,
              )
          assert captured["url"] == "https://api.example.com/api/hooks/session-stop"
          assert captured["method"] == "POST"
          assert captured["auth"] == "Bearer mykey"
          assert captured["ct"] == "Application/json"

      def test_default_timeout_is_5(self):
          from utils import call_zie_memory_api
          captured = {}
          def fake_urlopen(req, timeout):
              captured["timeout"] = timeout
              return MagicMock()
          with patch("utils.urllib.request.urlopen", side_effect=fake_urlopen):
              call_zie_memory_api(
                  "https://api.example.com", "k", "/ep", {}
              )
          assert captured["timeout"] == 5
  ```
  Run: `make test-unit` — must FAIL (`call_zie_memory_api` not importable, `urllib` not imported in utils)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/utils.py — add import at top and append helper at end of file

  # Add to imports section:
  import urllib.request

  # Append after project_tmp_path() (and atomic_write if already added):

  def call_zie_memory_api(
      url: str,
      key: str,
      endpoint: str,
      payload: dict,
      timeout: int = 5,
  ) -> None:
      """POST payload as JSON to zie-memory API endpoint.

      Constructs the full URL as url+endpoint, sets Bearer auth and
      Content-Type headers, and calls urlopen. Re-raises on any error —
      callers are responsible for their own except/log blocks.
      """
      data = urllib.request.json.dumps(payload).encode() if False else __import__("json").dumps(payload).encode()
      req = urllib.request.Request(
          f"{url}{endpoint}",
          data=data,
          headers={
              "Authorization": f"Bearer {key}",
              "Content-Type": "application/json",
          },
          method="POST",
      )
      urllib.request.urlopen(req, timeout=timeout)
  ```

  Note: the `json.dumps` line above uses a plain `import json` call for clarity. The actual implementation should import `json` at the top of `utils.py`.

  Clean implementation to add to `utils.py`:
  ```python
  import json
  import urllib.request

  def call_zie_memory_api(
      url: str,
      key: str,
      endpoint: str,
      payload: dict,
      timeout: int = 5,
  ) -> None:
      """POST payload as JSON to zie-memory API endpoint.

      Constructs the full URL as url+endpoint, sets Bearer auth and
      Content-Type headers, and calls urlopen. Re-raises on any error —
      callers are responsible for their own except/log blocks.
      """
      data = json.dumps(payload).encode()
      req = urllib.request.Request(
          f"{url}{endpoint}",
          data=data,
          headers={
              "Authorization": f"Bearer {key}",
              "Content-Type": "application/json",
          },
          method="POST",
      )
      urllib.request.urlopen(req, timeout=timeout)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Remove the duplicated inline `json` import note from the code; confirm `import json` appears once at the top of `utils.py`.
  Run: `make test-unit` — still PASS

## Task 2: Replace inline urllib blocks in `session-learn.py` and `wip-checkpoint.py`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `session-learn.py` has no `urllib.request.Request(...)` block — replaced by single `call_zie_memory_api(api_url, api_key, "/api/hooks/session-stop", payload, timeout=5)` call
- `wip-checkpoint.py` has no `urllib.request.Request(...)` block — replaced by single `call_zie_memory_api(api_url, api_key, "/api/hooks/wip-update", payload, timeout=3)` call
- Each caller keeps its own `try/except Exception as e: print(...)` block
- All existing tests in `test_hooks_session_learn.py` and `test_hooks_wip_checkpoint.py` pass

**Files:**
- Modify: `hooks/session-learn.py`
- Modify: `hooks/wip-checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # test_hooks_session_learn.py — add to TestSessionLearnGuardrails

      def test_no_crash_with_valid_https_unreachable(self, tmp_path):
          """Hook must exit 0 even when API is unreachable — error is logged to stderr."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, env_overrides={
              "ZIE_MEMORY_API_KEY": "fake-key",
              "ZIE_MEMORY_API_URL": "https://localhost:19999",
          })
          assert r.returncode == 0

  # test_hooks_wip_checkpoint.py — add to TestWipCheckpointGuardrails

      def test_no_crash_with_valid_https_unreachable_on_fifth_edit(self, tmp_path):
          """Hook must exit 0 when API is unreachable on checkpoint trigger."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          counter_path(tmp_path.name).write_text("4")
          r = run_hook(tmp_cwd=cwd, env_overrides={
              "ZIE_MEMORY_API_KEY": "fake-key",
              "ZIE_MEMORY_API_URL": "https://localhost:19999",
          })
          assert r.returncode == 0
  ```
  Run: `make test-unit` — existing tests pass; new tests also pass (hooks already handle this). RED signal comes from removing `import urllib.request` from the callers and referencing `call_zie_memory_api` before it is imported — do that swap now.

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/session-learn.py — update import and replace urllib block

  # Change utils import line:
  from utils import parse_roadmap_now, atomic_write, call_zie_memory_api

  # Remove:  import urllib.request

  # Replace the try block (lines 48-65) with:
  try:
      payload = {
          "project": project,
          "wip_summary": wip_context,
      }
      call_zie_memory_api(api_url, api_key, "/api/hooks/session-stop", payload, timeout=5)
  except Exception as e:
      print(f"[zie-framework] session-learn: {e}", file=sys.stderr)
  ```

  ```python
  # hooks/wip-checkpoint.py — update import and replace urllib block

  # Change utils import line:
  from utils import parse_roadmap_now, project_tmp_path, call_zie_memory_api

  # Remove:  import urllib.request

  # Replace the try block (lines 62-82) with:
  try:
      payload = {
          "content": content,
          "priority": "project",
          "tags": ["wip", "checkpoint", project],
          "project": project,
          "force": True,
      }
      call_zie_memory_api(api_url, api_key, "/api/hooks/wip-update", payload, timeout=3)
  except Exception as e:
      print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm neither `session-learn.py` nor `wip-checkpoint.py` contain `urllib.request.Request`.
  Confirm `import urllib.request` is removed from both callers (it now lives only in `utils.py`).
  Run: `make test-unit` — still PASS

---
*Commit: `git add hooks/utils.py hooks/session-learn.py hooks/wip-checkpoint.py tests/unit/test_utils.py tests/unit/test_hooks_session_learn.py tests/unit/test_hooks_wip_checkpoint.py && git commit -m "fix: extract call_zie_memory_api helper, dedup urllib POST logic"`*
