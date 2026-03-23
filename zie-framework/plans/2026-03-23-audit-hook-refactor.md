---
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-hook-refactor.md
spec: specs/2026-03-23-audit-hook-refactor-design.md
---

# Plan: Hook Refactor — Shared Utils + /tmp Isolation

**Spec:** specs/2026-03-23-audit-hook-refactor-design.md
**Effort:** M
**Test runner:** pytest

## Tasks

### Task 1 — Create hooks/utils.py: parse_roadmap_now()
**RED:** Write `tests/unit/test_utils.py` with cases:
- missing ROADMAP file returns `[]`
- ROADMAP with no `## Now` header returns `[]`
- ROADMAP with empty Now section returns `[]`
- Now section with items returns cleaned list (markdown links stripped via `re.sub`)
- `lstrip("- [ ]")` / `lstrip("- [x]")` removes checkbox prefixes
- Only items under the first `## Now` header are returned (stops at next `##`)

**GREEN:** Create `hooks/utils.py` and implement `parse_roadmap_now(roadmap_path: Path) -> list[str]` — reads the file, iterates lines, sets `in_now` flag on `## *now*` header, breaks on next `##`, strips markdown links and checkbox prefixes from `- ` items.

**REFACTOR:** Ensure the function handles `roadmap_path` as `Path | str`; add module docstring noting this is a shared library, not a hook.

---

### Task 2 — Create hooks/utils.py: project_tmp_path()
**RED:** Add test cases to `tests/unit/test_utils.py`:
- `project_tmp_path("last-test", "my-project")` returns `Path("/tmp/zie-my-project-last-test")`
- `project_tmp_path("edit-count", "my project!")` returns `Path("/tmp/zie-my-project--edit-count")` (non-alphanumeric chars replaced by `-`)
- `project_tmp_path("x", "ABC")` returns `Path("/tmp/zie-ABC-x")` (case preserved)

**GREEN:** Add `project_tmp_path(name: str, project: str) -> Path` to `hooks/utils.py` — uses `re.sub(r'[^a-zA-Z0-9]', '-', project)` for `safe_project`, returns `Path(f"/tmp/zie-{safe_project}-{name}")`.

**REFACTOR:** Confirm `re` is imported at module level (not inside the function); add type hints; `make test-unit` green.

---

### Task 3 — Refactor session-resume.py: use parse_roadmap_now() + 200-line truncation
**RED:** Add test to `tests/unit/test_session_resume.py` (or extend existing):
- Pass a synthetic 250-line ROADMAP (Now section at line 5, items at lines 6-8, more content after line 100) and assert `parse_roadmap_now` is called with only the first 100 lines (mock or patch the file read to verify truncation).
- Assert `import re` does not appear inside any function body in `session-resume.py` (static check via `ast` or `grep`).

**GREEN:** In `session-resume.py`:
- Add `from hooks.utils import parse_roadmap_now` (adjust import path to `from utils import parse_roadmap_now` per hook sys.path convention).
- When reading ROADMAP: `lines = roadmap_file.read_text().splitlines(); if len(lines) > 200: lines = lines[:100]`.
- Replace the inline `parse_section(text, "now")` call (and its `lstrip` chain) with `parse_roadmap_now(roadmap_file)` — pass the truncated text via a temp file or refactor `parse_roadmap_now` to also accept a string/lines parameter.
- Move `import re` to the top-level import block.
- Annotate the top-level `except Exception: sys.exit(0)` with `# intentional — malformed event must not crash hook`.

**REFACTOR:** Remove the now-unused local `parse_section` function if `now_items` is the only caller of it with "now"; keep `parse_section` only if `next_items` / `done_items` still need it (those are out of scope for utils extraction — note inline).

---

### Task 4 — Refactor session-learn.py: use parse_roadmap_now() + project_tmp_path() + stderr logging
**RED:** Add/extend `tests/unit/test_session_learn.py`:
- Assert no `in_now` variable exists in `session-learn.py` (static check).
- Assert `import re` is not inside a function or loop (static/AST check).
- Assert the inner `except Exception: pass` block (urllib call) is replaced with `except Exception as e: print(...)` to stderr.

**GREEN:** In `session-learn.py`:
- Add `from utils import parse_roadmap_now`.
- Replace the 10-line `in_now` loop with: `lines = parse_roadmap_now(roadmap_file); wip_context = "; ".join(lines[:3])`.
- Move `import re` to the top-level import block.
- Change the `except Exception: pass  # Never crash on stop` at the urllib block to `except Exception as e: print(f"[zie-framework] session-learn: {e}", file=sys.stderr)`.
- Annotate top-level `except Exception: sys.exit(0)` with `# intentional — malformed event must not crash hook`.

**REFACTOR:** Confirm `wip_context` assignment is still correct (empty string when `lines` is empty). `make test-unit` green.

---

### Task 5 — Refactor wip-checkpoint.py: use parse_roadmap_now() + project_tmp_path() + stderr logging
**RED:** Add/extend `tests/unit/test_wip_checkpoint.py`:
- Assert no hardcoded `/tmp/zie-framework-edit-count` literal in source (static check).
- Assert no `in_now` variable in source (static check).
- Assert inner `except Exception: pass` is replaced with stderr logging.

**GREEN:** In `wip-checkpoint.py`:
- Add `from utils import parse_roadmap_now, project_tmp_path`.
- Replace `counter_file = Path("/tmp/zie-framework-edit-count")` with `counter_file = project_tmp_path("edit-count", cwd.name)`.
- Replace the inline `in_now` loop (lines 52-61) with `lines = parse_roadmap_now(roadmap_file); wip_summary = "; ".join(lines[:3])`.
- Change `except Exception: pass  # Never crash the hook` at urllib block to `except Exception as e: print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)`.
- Change bare `except Exception: pass` on the counter read to `except Exception as e: print(f"[zie-framework] wip-checkpoint: {e}", file=sys.stderr)`.
- Annotate top-level `except Exception: sys.exit(0)` with `# intentional — malformed event must not crash hook`.

**REFACTOR:** `make test-unit` green; confirm no `/tmp/zie-framework-*` literals remain.

---

### Task 6 — Refactor auto-test.py: remove dead pass block + use project_tmp_path()
**RED:** Add/extend `tests/unit/test_auto_test.py`:
- Assert no hardcoded `/tmp/zie-framework-last-test` literal in source (static check).
- Assert the dead `pass` block at lines 53-56 (the `if "test_" in changed.name ...` branch that only contains `pass`) is removed — the branch either has real logic or is deleted.

**GREEN:** In `auto-test.py`:
- Add `from utils import project_tmp_path`.
- Replace `debounce_file = Path("/tmp/zie-framework-last-test")` with `debounce_file = project_tmp_path("last-test", cwd.name)`.
- Remove lines 53-56: delete the `if "test_" in changed.name or ...` block that contains only `pass` and the comment `# Still run but don't try to find matching module`. The `find_matching_test` function already handles test files gracefully by returning `None`.
- Change bare `except Exception as e: pass` at line 132 to `except Exception as e: print(f"[zie-framework] auto-test: {e}", file=sys.stderr)`.
- Annotate top-level `except Exception: sys.exit(0)` with `# intentional — malformed event must not crash hook`.

**REFACTOR:** Verify `find_matching_test` still handles test files correctly without the removed guard. `make test-unit` green.

---

### Task 7 — Fix intent-detect.py: pre-compile patterns + document hook output protocol
**RED:** Add `tests/unit/test_intent_detect.py` (or extend):
- Assert `COMPILED_PATTERNS` exists at module level in `intent-detect.py` (import and `hasattr` check).
- Assert `COMPILED_PATTERNS` values are lists of `re.Pattern` objects (not raw strings).
- Assert the scoring loop calls `.search(message)` on compiled pattern objects (static check or integration test using mock stdin).
- Assert `import re` does not appear inside a function or loop (static check).

**GREEN:** In `intent-detect.py`:
- Add `COMPILED_PATTERNS = {cat: [re.compile(p) for p in pats] for cat, pats in PATTERNS.items()}` immediately after the `PATTERNS` dict definition.
- Replace the scoring loop body `if re.search(pattern, message)` with `if compiled_pat.search(message)` iterating over `COMPILED_PATTERNS[category]`.
- `import re` is already at top-level — confirm it stays there.

For hook output protocol documentation, add a comment block to `hooks/hooks.json` (as a `"_comment"` key in the root object, since JSON doesn't support comments) or add a `HOOK_OUTPUT_PROTOCOL` constant string at the top of each hook. Preferred: add `"_hook_output_protocol"` doc key to `hooks.json` mapping each event type to its expected output format:
- `SessionStart` → plain text (printed to stdout, injected as session context)
- `UserPromptSubmit` → JSON `{"additionalContext": "..."}` printed to stdout
- `PostToolUse` → plain text warnings printed to stdout
- `Stop` → no output required; side-effects only

**REFACTOR:** Confirm all pattern categories in `COMPILED_PATTERNS` match `PATTERNS` keys exactly. `make test-unit` green.

---

### Task 8 — Add session-cleanup.py Stop hook for /tmp cleanup
**RED:** Add `tests/unit/test_session_cleanup.py`:
- Mock `CLAUDE_CWD` env var and create synthetic `/tmp/zie-{project}-*` files; assert `session-cleanup.py` deletes them.
- Assert files for a different project (different prefix) are NOT deleted.
- Assert the script exits cleanly (exit code 0) even when no matching files exist.
- Assert malformed stdin does not crash the script (top-level JSON parse guard).

**GREEN:** Create `hooks/session-cleanup.py`:
```python
#!/usr/bin/env python3
"""Stop hook — remove project-scoped /tmp files on session end."""
import sys
import json
import os
from pathlib import Path

try:
    event = json.loads(sys.stdin.read())
except Exception:
    # intentional — malformed event must not crash hook
    sys.exit(0)

cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
import re
safe_project = re.sub(r'[^a-zA-Z0-9]', '-', cwd.name)
pattern = f"/tmp/zie-{safe_project}-*"

for tmp_file in Path("/tmp").glob(f"zie-{safe_project}-*"):
    try:
        tmp_file.unlink()
    except Exception as e:
        print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)
```

Add a second Stop hook entry to `hooks/hooks.json` under the `Stop` event array, after the existing `session-learn.py` entry:
```json
{
  "type": "command",
  "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\""
}
```

Also add the `"_hook_output_protocol"` doc key to `hooks.json` (from Task 7).

**REFACTOR:** Move `import re` to top of `session-cleanup.py` (above the `try` block). Confirm `utils.project_tmp_path` and `session-cleanup.py` use the same `safe_project` transformation — extract to utils if divergence is detected. `make test-unit` green.
