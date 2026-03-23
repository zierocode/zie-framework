---
approved: true
approved_at: 2026-03-24
backlog: backlog/permission-request-auto-approve.md
---

# PermissionRequest Auto-Approve Safe SDLC Operations — Design Spec

**Problem:** Claude Code interrupts the TDD loop with permission prompts for
routine SDLC operations (`git add`, `git commit`, `make test-unit`,
`python3 -m pytest`), breaking flow dozens of times per session.

**Approach:** Add a new `PermissionRequest` hook (`hooks/sdlc-permissions.py`)
that matches `Bash` tool calls against a curated allowlist of safe SDLC
patterns. When a match is found, the hook outputs a JSON decision with
`behavior: "allow"` and `updatedPermissions` scoped to `destination: "session"`,
so the approval persists for the entire session and no subsequent prompt fires
for the same command pattern. Non-matching commands fall through to Claude's
default permission handling without interference.

**Components:**

- `hooks/sdlc-permissions.py` — new hook (PermissionRequest event, Bash matcher)
- `hooks/hooks.json` — new `PermissionRequest` stanza with `matcher: "Bash"`
- `tests/test_sdlc_permissions.py` — new unit test module

---

## Data Flow

1. Claude Code fires a `PermissionRequest` event before executing any `Bash`
   tool call that requires user permission.
2. `sdlc-permissions.py` reads the event from stdin via `read_event()`.
3. Hook checks `event["tool_name"]` — if not `"Bash"`, `sys.exit(0)`.
4. Hook extracts `event["tool_input"]["command"]` — if missing, `sys.exit(0)`.
5. Command string is whitespace-normalised:
   `cmd = re.sub(r'\s+', ' ', command.strip())` (case-sensitive — these
   commands are case-sensitive on the target shell).
6. Hook iterates the `SAFE_PATTERNS` list (ordered, compiled `re.Pattern`
   objects). First match wins.
7. **On match:** hook prints a JSON object to stdout and exits 0:
   ```json
   {
     "decision": {
       "behavior": "allow",
       "updatedPermissions": {
         "destination": "session",
         "permissions": [{"tool": "Bash", "command": "<matched_pattern>"}]
       }
     }
   }
   ```
8. **No match:** hook prints nothing and exits 0. Claude Code falls through to
   its normal permission dialog.
9. All logic is wrapped in the two-tier guard (outer `except Exception →
   sys.exit(0)`, inner `except Exception as e → stderr log + sys.exit(0)`).

---

## Allowlist — `SAFE_PATTERNS`

Patterns are anchored at the start of the normalised command string (`re.match`)
to prevent substring spoofing (e.g., a long pipeline ending in `git commit`
must not match). Each pattern must be both necessary and sufficient to uniquely
describe a safe operation.

| Pattern (regex, `re.match`) | Covers |
| --- | --- |
| `r"git add\b"` | `git add .`, `git add -p`, `git add <file>` |
| `r"git commit\b"` | `git commit -m "..."`, `git commit --amend --no-edit` (but NOT `--no-verify` — blocked by safety-check.py) |
| `r"git diff\b"` | `git diff`, `git diff HEAD`, `git diff --staged` |
| `r"git status\b"` | `git status`, `git status --short` |
| `r"git log\b"` | `git log`, `git log --oneline` |
| `r"git stash\b"` | `git stash`, `git stash pop`, `git stash list` |
| `r"make test"` | `make test`, `make test-unit`, `make test-integration` |
| `r"make lint"` | `make lint`, `make lint-fix` |
| `r"python3 -m pytest\b"` | `python3 -m pytest`, `python3 -m pytest -v`, `python3 -m pytest tests/` |
| `r"python3 -m bandit\b"` | `python3 -m bandit -r .` |

**Explicitly NOT in the allowlist** (must still prompt):

- `git push` (any form)
- `git merge` / `git rebase`
- `git reset` (blocked upstream by `safety-check.py`)
- `make release` / `make ship`
- Any command containing `--no-verify` (blocked upstream by `safety-check.py`)

The `safety-check.py` `BLOCKS` list fires on `PreToolUse` before the
`PermissionRequest` event, so there is no risk of auto-approving a
simultaneously-blocked command. The two hooks are complementary, not
overlapping.

---

## Edge Cases

- **Compound commands (`&&`, `;`, `|`):** The match is against the full
  normalised command string. A compound like `make test && git push` starts
  with `make test` and would match — but `git push` is safe to allow since
  `safety-check.py` would have already blocked it at `PreToolUse` if needed.
  To be conservative, patterns use `re.match` on the full string, so
  `git push && git add .` does NOT match `r"git add\b"` (push comes first).
  Accept this conservative behaviour; users can always approve manually.
- **Whitespace variations:** `re.sub(r'\s+', ' ', ...)` normalises tabs and
  multi-spaces before matching. Newlines inside a heredoc are not a concern
  since the command field is a single command string, not a shell script block.
- **Empty command:** Guard at step 4 ensures `sys.exit(0)` before matching.
- **PermissionRequest for non-Bash tools (e.g., Write, Edit):** Guard at
  step 3 passes through immediately — no false approvals for file writes.
- **Hook receives malformed JSON:** Outer guard in `read_event()` calls
  `sys.exit(0)` — Claude is never blocked.
- **Session persistence:** `destination: "session"` means the rule is cached
  by Claude Code for the session. If the session restarts, the hook fires again
  on first use — no stale state accumulates across sessions.
- **`updatedPermissions` schema variance:** If the Claude Code protocol evolves,
  the hook may output an unrecognised schema; Claude will fall back to prompting.
  This is safe — the hook never blocks.

---

## Test Plan (`tests/test_sdlc_permissions.py`)

All tests use the existing pattern: construct a JSON event dict, pass it as
stdin to `sdlc-permissions.py` via `subprocess.run`, and assert stdout/exit code.

| Test | Input | Expected stdout | Expected exit |
| --- | --- | --- | --- |
| `test_git_add_approved` | `git add .` | JSON with `behavior: "allow"` | 0 |
| `test_git_commit_approved` | `git commit -m "feat: x"` | JSON with `behavior: "allow"` | 0 |
| `test_make_test_unit_approved` | `make test-unit` | JSON with `behavior: "allow"` | 0 |
| `test_pytest_approved` | `python3 -m pytest -v tests/` | JSON with `behavior: "allow"` | 0 |
| `test_bandit_approved` | `python3 -m bandit -r .` | JSON with `behavior: "allow"` | 0 |
| `test_git_push_not_approved` | `git push origin dev` | empty stdout | 0 |
| `test_git_merge_not_approved` | `git merge main` | empty stdout | 0 |
| `test_make_release_not_approved` | `make release NEW=v1.0.0` | empty stdout | 0 |
| `test_non_bash_tool_passthrough` | `tool_name: "Write"` | empty stdout | 0 |
| `test_empty_command_passthrough` | `command: ""` | empty stdout | 0 |
| `test_malformed_json_passthrough` | `stdin: "{"` | empty stdout | 0 |
| `test_session_destination_in_output` | `git add .` | `updatedPermissions.destination == "session"` | 0 |
| `test_compound_push_first_not_approved` | `git push && git add .` | empty stdout | 0 |

---

## Out of Scope

- **Notification hook for permission logging** — tracked separately in
  `backlog/notification-hook-intercept.md`. That hook is async, observational,
  and targets the `Notification` event; this hook targets `PermissionRequest`.
  They are complementary but must be developed independently.
- **User-configurable allowlist** — no `.config` extension in this iteration.
  The allowlist is hardcoded in `sdlc-permissions.py`. A configurable layer
  (e.g., reading extra patterns from `.zie-config`) is a future enhancement.
- **Non-Bash tool auto-approval** — `Write`, `Edit`, and `Read` tool
  permissions are not in scope; only `Bash` SDLC operations are targeted.
- **Cross-session persistence** — `destination: "session"` is the correct
  scope. Writing approvals to disk for cross-session reuse is not in scope and
  would reduce safety.
- **UI or command to manage the allowlist at runtime** — no `/zie-permissions`
  command in this iteration (referenced in the Notification hook backlog item
  as a future affordance).
