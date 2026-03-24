---
approved: true
approved_at: 2026-03-24
backlog: backlog/permission-request-auto-approve.md
spec: specs/2026-03-24-permission-request-auto-approve-design.md
---

# PermissionRequest Auto-Approve Safe SDLC Operations — Implementation Plan

**Goal:** Add a `PermissionRequest` hook (`hooks/sdlc-permissions.py`) that auto-approves a curated allowlist of safe SDLC `Bash` commands — `git add`, `git commit`, `make test*`, `python3 -m pytest`, etc. — eliminating repeated permission prompts during TDD loops. Non-matching commands fall through to Claude's default dialog without interference.

**Architecture:** New hook reads the `PermissionRequest` event from stdin via `read_event()`, checks `tool_name == "Bash"`, whitespace-normalises the command string, and runs it against `SAFE_PATTERNS` (ordered list of compiled `re.Pattern` objects, anchored with `re.match`). On first match it prints a JSON `decision` object with `behavior: "allow"` and `updatedPermissions.destination: "session"` then exits 0. On no match it prints nothing and exits 0. Two-tier guard prevents any crash from ever blocking Claude.

**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/sdlc-permissions.py` | New PermissionRequest hook — allowlist matcher + JSON decision output |
| Modify | `hooks/hooks.json` | Add `PermissionRequest` stanza with `matcher: "Bash"` |
| Create | `tests/unit/test_sdlc_permissions.py` | Full unit test suite for the new hook |

---

## Task 1: Create `hooks/sdlc-permissions.py`

<!-- depends_on: none -->

**Acceptance Criteria:**

- Hook outputs `{"decision": {"behavior": "allow", "updatedPermissions": {"destination": "session", "permissions": [{"tool": "Bash", "command": "<pattern>"}]}}}` for every pattern in `SAFE_PATTERNS` when matched
- Hook outputs empty stdout (no bytes) for commands not in the allowlist (`git push`, `git merge`, `make release`)
- Hook outputs empty stdout for `tool_name != "Bash"` (e.g., `"Write"`)
- Hook outputs empty stdout and exits 0 for an empty command string
- Hook outputs empty stdout and exits 0 for malformed JSON on stdin
- All exit codes are 0 — hook never blocks Claude
- `destination` in `updatedPermissions` is exactly `"session"`
- `re.match` anchoring prevents a compound command starting with a non-safe token (e.g., `git push && git add .`) from matching a safe pattern

**Files:**

- Create: `hooks/sdlc-permissions.py`
- Create: `tests/unit/test_sdlc_permissions.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_sdlc_permissions.py

  """Tests for hooks/sdlc-permissions.py"""
  import json
  import os
  import subprocess
  import sys

  import pytest

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


  def run_hook(command, tool_name="Bash"):
      hook = os.path.join(REPO_ROOT, "hooks", "sdlc-permissions.py")
      event = {"tool_name": tool_name, "tool_input": {"command": command}}
      return subprocess.run(
          [sys.executable, hook],
          input=json.dumps(event),
          capture_output=True,
          text=True,
      )


  def run_hook_raw(stdin_text):
      """Pass arbitrary stdin bytes — used for malformed-JSON test."""
      hook = os.path.join(REPO_ROOT, "hooks", "sdlc-permissions.py")
      return subprocess.run(
          [sys.executable, hook],
          input=stdin_text,
          capture_output=True,
          text=True,
      )


  def assert_approved(r):
      assert r.returncode == 0
      payload = json.loads(r.stdout)
      assert payload["decision"]["behavior"] == "allow"


  def assert_passthrough(r):
      assert r.returncode == 0
      assert r.stdout.strip() == ""


  # ---------------------------------------------------------------------------
  # Allowlist — commands that MUST be auto-approved
  # ---------------------------------------------------------------------------

  class TestAllowlistApproved:
      def test_git_add_dot_approved(self):
          assert_approved(run_hook("git add ."))

      def test_git_add_file_approved(self):
          assert_approved(run_hook("git add hooks/sdlc-permissions.py"))

      def test_git_add_patch_approved(self):
          assert_approved(run_hook("git add -p"))

      def test_git_commit_message_approved(self):
          assert_approved(run_hook('git commit -m "feat: add sdlc permissions hook"'))

      def test_git_commit_amend_no_edit_approved(self):
          assert_approved(run_hook("git commit --amend --no-edit"))

      def test_git_diff_approved(self):
          assert_approved(run_hook("git diff"))

      def test_git_diff_head_approved(self):
          assert_approved(run_hook("git diff HEAD"))

      def test_git_diff_staged_approved(self):
          assert_approved(run_hook("git diff --staged"))

      def test_git_status_approved(self):
          assert_approved(run_hook("git status"))

      def test_git_status_short_approved(self):
          assert_approved(run_hook("git status --short"))

      def test_git_log_approved(self):
          assert_approved(run_hook("git log"))

      def test_git_log_oneline_approved(self):
          assert_approved(run_hook("git log --oneline"))

      def test_git_stash_approved(self):
          assert_approved(run_hook("git stash"))

      def test_git_stash_pop_approved(self):
          assert_approved(run_hook("git stash pop"))

      def test_git_stash_list_approved(self):
          assert_approved(run_hook("git stash list"))

      def test_make_test_approved(self):
          assert_approved(run_hook("make test"))

      def test_make_test_unit_approved(self):
          assert_approved(run_hook("make test-unit"))

      def test_make_test_integration_approved(self):
          assert_approved(run_hook("make test-integration"))

      def test_make_lint_approved(self):
          assert_approved(run_hook("make lint"))

      def test_make_lint_fix_approved(self):
          assert_approved(run_hook("make lint-fix"))

      def test_pytest_approved(self):
          assert_approved(run_hook("python3 -m pytest"))

      def test_pytest_verbose_approved(self):
          assert_approved(run_hook("python3 -m pytest -v"))

      def test_pytest_path_approved(self):
          assert_approved(run_hook("python3 -m pytest tests/"))

      def test_bandit_approved(self):
          assert_approved(run_hook("python3 -m bandit -r ."))


  # ---------------------------------------------------------------------------
  # Commands explicitly NOT in the allowlist — must pass through (empty stdout)
  # ---------------------------------------------------------------------------

  class TestDenylistPassthrough:
      def test_git_push_not_approved(self):
          assert_passthrough(run_hook("git push origin dev"))

      def test_git_push_bare_not_approved(self):
          assert_passthrough(run_hook("git push"))

      def test_git_merge_not_approved(self):
          assert_passthrough(run_hook("git merge main"))

      def test_git_rebase_not_approved(self):
          assert_passthrough(run_hook("git rebase dev"))

      def test_make_release_not_approved(self):
          assert_passthrough(run_hook("make release NEW=v1.0.0"))

      def test_make_ship_not_approved(self):
          assert_passthrough(run_hook("make ship"))


  # ---------------------------------------------------------------------------
  # Guard cases — tool_name, empty command, malformed JSON
  # ---------------------------------------------------------------------------

  class TestGuardPassthrough:
      def test_non_bash_tool_passthrough(self):
          assert_passthrough(run_hook("git add .", tool_name="Write"))

      def test_non_bash_edit_tool_passthrough(self):
          assert_passthrough(run_hook("git add .", tool_name="Edit"))

      def test_empty_command_passthrough(self):
          r = run_hook("")
          assert_passthrough(r)

      def test_malformed_json_passthrough(self):
          r = run_hook_raw("{not valid json")
          assert_passthrough(r)

      def test_missing_tool_input_passthrough(self):
          hook = os.path.join(REPO_ROOT, "hooks", "sdlc-permissions.py")
          event = {"tool_name": "Bash"}  # no tool_input key
          r = subprocess.run(
              [sys.executable, hook],
              input=json.dumps(event),
              capture_output=True,
              text=True,
          )
          assert_passthrough(r)


  # ---------------------------------------------------------------------------
  # Output schema — session destination and permissions list shape
  # ---------------------------------------------------------------------------

  class TestOutputSchema:
      def test_session_destination_in_output(self):
          r = run_hook("git add .")
          payload = json.loads(r.stdout)
          assert payload["decision"]["updatedPermissions"]["destination"] == "session"

      def test_permissions_list_contains_bash_tool(self):
          r = run_hook("git add .")
          payload = json.loads(r.stdout)
          perms = payload["decision"]["updatedPermissions"]["permissions"]
          assert isinstance(perms, list)
          assert len(perms) == 1
          assert perms[0]["tool"] == "Bash"

      def test_permissions_command_field_present(self):
          r = run_hook("git add .")
          payload = json.loads(r.stdout)
          perms = payload["decision"]["updatedPermissions"]["permissions"]
          assert "command" in perms[0]

      def test_exit_code_always_zero_on_allow(self):
          r = run_hook("make test-unit")
          assert r.returncode == 0

      def test_exit_code_always_zero_on_passthrough(self):
          r = run_hook("git push origin dev")
          assert r.returncode == 0


  # ---------------------------------------------------------------------------
  # Anchoring — compound commands must not spoof a safe prefix
  # ---------------------------------------------------------------------------

  class TestAnchoringBehaviour:
      def test_compound_push_first_not_approved(self):
          # git push comes first — re.match on full string must NOT match git add\b
          assert_passthrough(run_hook("git push && git add ."))

      def test_compound_release_first_not_approved(self):
          assert_passthrough(run_hook("make release && make test"))

      def test_whitespace_normalisation_still_approves(self):
          # Extra spaces between tokens — normalise then match
          assert_approved(run_hook("git  add  ."))

      def test_tab_normalisation_still_approves(self):
          assert_approved(run_hook("git\tadd\t."))
  ```

  Run: `make test-unit` — must **FAIL** (`sdlc-permissions.py` does not exist yet)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/sdlc-permissions.py

  #!/usr/bin/env python3
  """PermissionRequest:Bash hook — auto-approve safe SDLC operations."""
  import json
  import os
  import re
  import sys

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import read_event

  # Outer guard — parse event; any failure must exit 0 (never block Claude)
  try:
      event = read_event()
      tool_name = event.get("tool_name", "")
      if tool_name != "Bash":
          sys.exit(0)
      command = (event.get("tool_input") or {}).get("command", "")
      if not command:
          sys.exit(0)
  except Exception:
      sys.exit(0)

  # Inner operations — match and output decision
  try:
      cmd = re.sub(r'\s+', ' ', command.strip())

      SAFE_PATTERNS = [
          r"git add\b",
          r"git commit\b",
          r"git diff\b",
          r"git status\b",
          r"git log\b",
          r"git stash\b",
          r"make test",
          r"make lint",
          r"python3 -m pytest\b",
          r"python3 -m bandit\b",
      ]

      matched_pattern = None
      for pattern in SAFE_PATTERNS:
          if re.match(pattern, cmd):
              matched_pattern = pattern
              break

      if matched_pattern:
          decision = {
              "decision": {
                  "behavior": "allow",
                  "updatedPermissions": {
                      "destination": "session",
                      "permissions": [
                          {"tool": "Bash", "command": matched_pattern}
                      ],
                  },
              }
          }
          print(json.dumps(decision))

  except Exception as e:
      print(f"[zie-framework] sdlc-permissions: {e}", file=sys.stderr)

  sys.exit(0)
  ```

  Run: `make test-unit` — must **PASS**

---

- [ ] **Step 3: Refactor**

  - Verify `SAFE_PATTERNS` is defined at module level (not inside the try block) so it reads as a clear configuration constant. Move it above the `try` block if the GREEN implementation placed it inside.
  - Confirm the outer guard and inner operations are clearly separated by a blank line and comment.
  - No logic changes — patterns, anchoring, and output schema remain identical.

  Run: `make test-unit` — still **PASS**

---

## Task 2: Register `PermissionRequest` in `hooks.json`

<!-- depends_on: Task 1 (hook file must exist before registering) -->

**Acceptance Criteria:**

- `hooks.json` contains a `"PermissionRequest"` top-level key
- The stanza has `"matcher": "Bash"` and a single `command` entry pointing to `sdlc-permissions.py` via `${CLAUDE_PLUGIN_ROOT}`
- All existing hook stanzas (`SessionStart`, `UserPromptSubmit`, `PostToolUse`, `PreToolUse`, `Stop`) are unchanged
- JSON is valid (no trailing commas, correct braces)

**Files:**

- Modify: `hooks/hooks.json`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_sdlc_permissions.py — add new class at end of file

  class TestHooksJsonRegistration:
      def test_permission_request_stanza_exists(self):
          hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
          with open(hooks_path) as f:
              hooks = json.load(f)
          assert "PermissionRequest" in hooks["hooks"], (
              "PermissionRequest stanza missing from hooks.json"
          )

      def test_permission_request_matcher_is_bash(self):
          hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
          with open(hooks_path) as f:
              hooks = json.load(f)
          stanza = hooks["hooks"]["PermissionRequest"]
          assert isinstance(stanza, list)
          assert stanza[0]["matcher"] == "Bash"

      def test_permission_request_command_points_to_hook(self):
          hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
          with open(hooks_path) as f:
              hooks = json.load(f)
          stanza = hooks["hooks"]["PermissionRequest"]
          cmd = stanza[0]["hooks"][0]["command"]
          assert "sdlc-permissions.py" in cmd

      def test_permission_request_uses_plugin_root_var(self):
          hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
          with open(hooks_path) as f:
              hooks = json.load(f)
          stanza = hooks["hooks"]["PermissionRequest"]
          cmd = stanza[0]["hooks"][0]["command"]
          assert "${CLAUDE_PLUGIN_ROOT}" in cmd

      def test_existing_stanzas_intact(self):
          hooks_path = os.path.join(REPO_ROOT, "hooks", "hooks.json")
          with open(hooks_path) as f:
              hooks = json.load(f)
          for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
              assert key in hooks["hooks"], f"Existing stanza '{key}' was removed from hooks.json"
  ```

  Run: `make test-unit` — must **FAIL** (`PermissionRequest` key absent)

---

- [ ] **Step 2: Implement (GREEN)**

  Add the `PermissionRequest` stanza to `hooks/hooks.json`. Insert it after the `PreToolUse` block and before `Stop`, keeping the existing structure intact:

  ```json
  "PermissionRequest": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/sdlc-permissions.py\""
        }
      ]
    }
  ],
  ```

  Full updated `hooks.json` with the new stanza in place:

  ```json
  {
    "_hook_output_protocol": {
      "SessionStart": "plain text printed to stdout — injected as session context",
      "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
      "PostToolUse": "plain text warnings/status printed to stdout",
      "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
      "PermissionRequest": "JSON {\"decision\": {\"behavior\": \"allow\", \"updatedPermissions\": {...}}} printed to stdout",
      "Stop": "no output required; side-effects only (file writes, API calls)"
    },
    "hooks": {
      "SessionStart": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-resume.py\""
            }
          ]
        }
      ],
      "UserPromptSubmit": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-detect.py\""
            }
          ]
        }
      ],
      "PostToolUse": [
        {
          "matcher": "Edit|Write",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/auto-test.py\""
            },
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/wip-checkpoint.py\""
            }
          ]
        }
      ],
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety-check.py\""
            }
          ]
        }
      ],
      "PermissionRequest": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/sdlc-permissions.py\""
            }
          ]
        }
      ],
      "Stop": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\""
            },
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\""
            }
          ]
        }
      ]
    }
  }
  ```

  Run: `make test-unit` — must **PASS**

---

- [ ] **Step 3: Refactor**

  - Add the `"PermissionRequest"` protocol note to `_hook_output_protocol` (included in the GREEN JSON above) so the header comment stays in sync with all registered events.
  - No logic changes.

  Run: `make test-unit` — still **PASS**

---

## Commit

```
git add hooks/sdlc-permissions.py hooks/hooks.json tests/unit/test_sdlc_permissions.py
git commit -m "feat: PermissionRequest hook — auto-approve safe SDLC Bash operations"
```
