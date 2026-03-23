---
approved: true
approved_at: 2026-03-24
backlog: backlog/stop-uncommitted-guard.md
---

# Stop Hook Uncommitted Work Guard — Design Spec

**Problem:** When Claude finishes a response, implementation files may be
written but uncommitted, causing work to be silently lost if the session ends
or compacts.

**Approach:** A new `hooks/stop-guard.py` runs on every `Stop` event, executes
`git status --short` in the project CWD, and filters the output for
implementation files matching the project's canonical path patterns. If matches
are found and the event's `stop_hook_active` field is not set, the hook emits a
`decision: "block"` JSON response listing the uncommitted files and a concrete
commit command, causing Claude to continue and commit before the turn ends. The
`stop_hook_active` guard prevents the block from re-triggering on the
immediately following Stop event, breaking the infinite-loop risk inherent to
self-blocking Stop hooks.

**Components:**

- `hooks/stop-guard.py` — new hook (primary deliverable)
- `hooks/hooks.json` — add `stop-guard.py` as the first entry in the `Stop`
  hook list (runs before `session-learn.py` and `session-cleanup.py`)
- `hooks/utils.py` — no changes needed; `read_event()` and `get_cwd()` are
  reused as-is
- `tests/test_stop_guard.py` — new unit test module
- `zie-framework/project/components.md` — add `stop-guard.py` row to Hooks
  table

**Data Flow:**

1. Claude finishes generating a response; Claude Code fires the `Stop` event.
2. Claude Code invokes `stop-guard.py` with the event JSON on stdin.
3. **Outer guard** — `read_event()` parses stdin into `event: dict`. On any
   parse failure, `sys.exit(0)` immediately (ADR-003: never crash/block Claude).
4. Check `event.get("stop_hook_active")` — if truthy, `sys.exit(0)` immediately.
   This is the infinite-loop breaker: Claude Code sets this flag on the Stop
   event that fires after a hook-triggered continuation, so the guard fires at
   most once per original response.
5. **Inner operations** — call `get_cwd()` to obtain the project root. Run
   `subprocess.run(["git", "status", "--short"], cwd=cwd, capture_output=True,
   text=True, timeout=5)`. On any `Exception` (git not found, not a repo,
   timeout), log to stderr and `sys.exit(0)`.
6. Parse stdout line-by-line. Each line has the form `XY path` (two-char status
   code + space + path). Extract the path token (index `[3:]`). Keep lines
   where `XY` is not `??` (untracked new files outside the project are ignored
   only if they don't match the filter; see step 7) and the path matches at
   least one implementation glob pattern:
   - `hooks/*.py`
   - `tests/*.py`
   - `commands/*.md`
   - `skills/**/*.md`
   - `templates/**/*`
7. Untracked files (`??` prefix) that match the patterns above are included —
   a new hook script that was never staged is still uncommitted work.
8. If no matching paths remain, `sys.exit(0)` — clean tree, no block.
9. Build the block payload:
   ```json
   {
     "decision": "block",
     "reason": "Uncommitted implementation files detected:\n  hooks/foo.py\n  tests/test_foo.py\n\nCommit this work before ending:\n  git add -A && git commit -m 'feat: <describe change>'"
   }
   ```
   Print the JSON to stdout and `sys.exit(0)`. Claude Code reads the `decision:
   "block"` response, feeds the reason back to Claude, and Claude continues to
   commit.

**Edge Cases:**

- `stop_hook_active` is truthy — exit 0 immediately; no git call, no block.
  Prevents infinite loop where Claude tries to commit, triggers another Stop,
  guard fires again, blocks again.
- Not a git repository (`git status` exits non-zero or raises) — catch
  `subprocess.CalledProcessError` and `Exception`; log to stderr; exit 0.
  Guard must not block in non-git projects.
- `git` binary not on PATH — `FileNotFoundError` caught by outer `except
  Exception`; exit 0.
- `git status` timeout (e.g., slow NFS mount, large repo) — `subprocess.run`
  called with `timeout=5`; `subprocess.TimeoutExpired` caught; exit 0.
- Repo root differs from `CLAUDE_CWD` (hook runs inside a monorepo sub-dir) —
  `get_cwd()` returns `CLAUDE_CWD`; `git status --short` with that cwd still
  returns paths relative to the repo root, not sub-dir. The path filter uses
  `fnmatch` against the raw path token; patterns like `hooks/*.py` will only
  match if the token is `hooks/foo.py` (not `sub/hooks/foo.py`). This is
  acceptable for the primary use case (projects where zie-framework is installed
  at repo root). Deep-nesting support is out of scope.
- Only documentation files changed (e.g., `ROADMAP.md`, `zie-framework/**/*.md`
  other than `commands/` and `skills/`) — these are not in the filter patterns;
  guard does not block on docs-only changes.
- Staged + unstaged mix — `git status --short` reports both; both are caught by
  the status code check (staged: `M `, `A `, `D `; unstaged: ` M`, ` D`;
  untracked: `??`). All are considered uncommitted until `git commit` runs.
- Empty CWD or CWD does not exist — `subprocess.run` raises `FileNotFoundError`
  or `NotADirectoryError`; caught by `except Exception`; exit 0.
- Claude commits mid-loop then Stop fires again — `git status` returns clean;
  guard finds no matching paths; exits 0; session ends normally.

**Out of Scope:**

- Blocking on documentation-only changes (`ROADMAP.md`, `PROJECT.md`,
  `zie-framework/project/*.md`, `decisions/*.md`) — these are not
  implementation files; noisy false positives.
- Suggesting which commit message to use beyond the generic `feat: <describe
  change>` placeholder — message composition is Claude's responsibility.
- Auto-committing without Claude's confirmation — the block only prompts;
  Claude executes the commit.
- Support for multiple simultaneous Stop hook blocks (chaining) — only
  `stop-guard.py` uses `decision: block`; other Stop hooks remain side-effect
  only.
- Configurable path filters per project — patterns are hardcoded to the
  zie-framework canonical layout; per-project overrides via `.config` are not
  implemented in this iteration.
- Handling detached HEAD or bare repos — treated the same as "git error"; guard
  exits 0 without blocking.
