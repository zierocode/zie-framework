---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-notification-log-double-guard.md
---

# lean-notification-log-double-guard — Implementation Plan

**Goal:** Remove the redundant inner `if notification_type == "permission_prompt":` guard from `notification-log.py` and de-indent the inner operations block, since the `hooks.json` matcher and the outer guard already guarantee only `permission_prompt` events reach that code.

**Architecture:** This is a single-file code-smell fix. No logic changes, no new modules, no new tests — existing tests cover all behaviours and will continue to pass after de-indenting. A one-line comment is added to the inner block to explain why no type-check is needed.

**Tech Stack:** Python 3, pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/notification-log.py` | Remove inner type guard; de-indent block; add explanatory comment |

---

## Task 1: Remove inner type guard and de-indent operations block

**Acceptance Criteria:**
- `notification-log.py` has no `if notification_type == "permission_prompt":` inside the inner `try` block
- The operations block is de-indented by one level (4 spaces removed)
- A comment above the operations block reads: `# hooks.json matcher ensures only permission_prompt events reach here; no inner type check needed`
- `make test-unit` passes — all existing tests green
- `make lint` passes — no lint violations

**Files:**
- Modify: `hooks/notification-log.py`

- [ ] **Step 1: Write failing tests (RED)**

  The spec says no test changes are needed — existing tests already cover the behaviours. The RED step here is structural: confirm the current source contains the redundant inner type check before removing it.

  ```python
  # Verify redundant guard exists — run from repo root:
  python3 -c "
  from pathlib import Path
  src = Path('hooks/notification-log.py').read_text()
  assert 'if notification_type == \"permission_prompt\"' in src, 'Inner guard not found — already removed?'
  print('RED confirmed: inner type guard present')
  "
  ```

  Run: `make test-unit` — must PASS (baseline green before change)

- [ ] **Step 2: Implement (GREEN)**

  Edit `hooks/notification-log.py` — replace the inner operations block:

  **Before (lines 63–82):**
  ```python
  # --- Inner operations: file I/O; errors are logged, hook still exits 0 ---
  try:
      message = sanitize_log_field(event.get("message", ""))
      project = safe_project_name(get_cwd().name)

      if notification_type == "permission_prompt":
          log_path = project_tmp_path("permission-log", project)
          records = _append_and_write(log_path, message)
          count = sum(1 for r in records if r.get("msg") == message)
          if count >= 3:
              print(json.dumps({
                  "additionalContext": (
                      "This permission has been asked 3+ times this session. "
                      "Run /zie-permissions to add it to the allow list."
                  )
              }))


  except Exception as e:
      print(f"[zie-framework] notification-log: {e}", file=sys.stderr)
  ```

  **After:**
  ```python
  # --- Inner operations: file I/O; errors are logged, hook still exits 0 ---
  # hooks.json matcher ensures only permission_prompt events reach here; no inner type check needed
  try:
      message = sanitize_log_field(event.get("message", ""))
      project = safe_project_name(get_cwd().name)
      log_path = project_tmp_path("permission-log", project)
      records = _append_and_write(log_path, message)
      count = sum(1 for r in records if r.get("msg") == message)
      if count >= 3:
          print(json.dumps({
              "additionalContext": (
                  "This permission has been asked 3+ times this session. "
                  "Run /zie-permissions to add it to the allow list."
              )
          }))

  except Exception as e:
      print(f"[zie-framework] notification-log: {e}", file=sys.stderr)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Run lint check; no further structural changes needed.

  ```bash
  make lint
  ```

  Run: `make test-unit` — still PASS
