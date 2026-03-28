---
approved: true
approved_at: 2026-03-24
backlog: backlog/security-shell-injection.md
spec: specs/2026-03-24-security-shell-injection-design.md
---

# Security: Shell Injection Fix in input-sanitizer.py — Implementation Plan

**Goal:** Replace the shell-injection-vulnerable `echo "Would run: {command}"` display expression with a safe `printf "Would run: %s\n" {shlex.quote(command)}` form in `hooks/input-sanitizer.py`.
**Architecture:** A single-file change to `hooks/input-sanitizer.py` — add `import shlex` to the stdlib import block and swap the `echo` sub-expression for `printf` with `shlex.quote`. One parametrized test method covering commands with shell metacharacters (`"`, `'`, `;`, `&&`, `|`) is added to the existing test class in `tests/unit/test_input_sanitizer.py`. No new files, no new dependencies.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/input-sanitizer.py` | Add `import shlex`; replace `echo` with `printf` + `shlex.quote` |
| Modify | `tests/unit/test_input_sanitizer.py` | Add `test_confirm_rewrite_metacharacters_safe` parametrized test |

---

## Task 1: Fix shell injection in input-sanitizer.py

**Acceptance Criteria:**
- `hooks/input-sanitizer.py` imports `shlex` in the stdlib block (after `import re`, before `import sys`)
- The `rewritten` f-string uses `printf "Would run: %s\n" {shlex.quote(command)}` instead of `echo "Would run: {command}"`
- The inner exec block `{ {command}; }` remains unchanged (intentionally unquoted)
- `make test-unit` passes for all existing tests

**Files:**
- Modify: `hooks/input-sanitizer.py`
- Modify: `tests/unit/test_input_sanitizer.py`

---

- [ ] Step 1: Write failing tests (RED)

  ```python
  # Append inside class TestBashConfirmRewrite in tests/unit/test_input_sanitizer.py

  @pytest.mark.parametrize("command", [
      'rm -rf ./dist "quoted dir"',
      "rm -rf ./it's-mine",
      "rm -rf ./foo; evil",
      "rm -rf ./a && evil",
  ])
  def test_confirm_rewrite_metacharacters_safe(self, command):
      r = run_hook("Bash", {"command": command})
      # 1. Hook exits 0
      assert r.returncode == 0
      # 2. stdout is valid JSON with expected keys
      out = json.loads(r.stdout)
      assert "updatedInput" in out
      assert "permissionDecision" in out
      rewritten_cmd = out["updatedInput"]["command"]
      # 3. rewritten command uses printf form
      assert 'printf "Would run: %s\\n"' in rewritten_cmd
      # 4. does NOT contain bare echo with unquoted command value
      assert f'echo "Would run: {command}"' not in rewritten_cmd
      # 5. inner exec block contains original unquoted command
      assert f'{{ {command}; }}' in rewritten_cmd
  ```

  Run: `make test-unit` — must FAIL (`test_confirm_rewrite_metacharacters_safe` fails because the hook still uses `echo`)

---

- [ ] Step 2: Implement (GREEN)

  In `hooks/input-sanitizer.py`:

  **Import block (lines 12–15) — add `import shlex` after `import re`, before `import sys`:**

  ```python
  # BEFORE:
  import json
  import os
  import re
  import sys

  # AFTER:
  import json
  import os
  import re
  import shlex
  import sys
  ```

  **Rewrite block (lines 90–94) — replace the echo sub-expression:**

  ```python
  # BEFORE:
  rewritten = (
      f'echo "Would run: {command}" '
      f'&& read -p "Confirm? [y/N] " _y '
      f'&& [ "$_y" = "y" ] && {{ {command}; }}'
  )

  # AFTER:
  rewritten = (
      f'printf "Would run: %s\\n" {shlex.quote(command)} '
      f'&& read -p "Confirm? [y/N] " _y '
      f'&& [ "$_y" = "y" ] && {{ {command}; }}'
  )
  ```

  Run: `make test-unit` — must PASS

---

- [ ] Step 3: Refactor

  Verify the double-wrapping guard at line 82 (`if "Would run:" in command`) still functions correctly — `printf "Would run: %s\n"` contains the substring `"Would run:"` so the guard fires as expected on re-entrant calls. No code change needed.

  Check that `test_no_double_wrapping_on_reentrant_call` continues to pass with the updated hook (the existing `already_wrapped` fixture uses `echo` but the guard only checks for `"Would run:"`, which is present regardless).

  Run: `make test-unit` — still PASS

---

**Commit:** `git add hooks/input-sanitizer.py tests/unit/test_input_sanitizer.py && git commit -m "fix: security-shell-injection — replace echo with printf+shlex.quote in confirm rewrite"`
