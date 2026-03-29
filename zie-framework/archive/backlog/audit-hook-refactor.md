# audit: hook refactor — shared utils + /tmp isolation

## Problem

Three hooks (session-learn.py, wip-checkpoint.py, session-resume.py) contain ~40 LOC
of identical ROADMAP "Now" section parsing, copy-pasted. Any fix must be applied
in 3 places.

Two hooks use hardcoded global /tmp paths (`/tmp/zie-framework-last-test`,
`/tmp/zie-framework-edit-count`). Multiple Claude Code sessions open simultaneously
(different projects) share these files — cross-project debounce interference and
merged edit counters.

11 bare `except Exception: pass` statements swallow all errors silently across 5 hooks.
Dead code and style issues compound the maintenance burden.

## Motivation

ROADMAP parsing duplication means a format change (new ROADMAP section, markdown
link stripping tweak) requires touching 3 files. /tmp collision is a real runtime bug
for anyone with two projects open simultaneously.

## Scope

- Create `hooks/utils.py` — NOT a hook, a shared library:
  - `parse_roadmap_now(roadmap_path) -> list[str]`
  - `project_tmp_path(name: str, project: str) -> Path`
    → returns `/tmp/zie-{safe_project}-{name}` for per-project isolation
- Refactor session-learn.py, wip-checkpoint.py, session-resume.py to import utils
- Replace `/tmp/zie-framework-*` with `project_tmp_path(...)` calls
- Replace bare `except Exception: pass` with `except Exception: pass  # intentional`
  at JSON parse guards; inner logic exceptions write one line to stderr
- Add Stop hook cleanup: delete project-scoped tmp files on session end
- Remove dead `pass` block in auto-test.py:53-56
- Move `import re` to top-level in session-learn.py and session-resume.py
- Document hook output protocol in a comment block in hooks.json or README:
  which events expect plain text vs JSON `additionalContext` (finding #16)
- Add ReDoS guard in intent-detect.py: pre-compile patterns at module level
  so regex engine reuse eliminates repeated compilation overhead (finding #23)
- session-resume.py: add early-exit if ROADMAP.md is large (>200 lines) with
  truncation to first 100 lines to keep SessionStart fast (finding #28)

## Prevention mechanism

`utils.py` is the single source of truth for ROADMAP parsing. All edge cases
(missing header, empty Now, malformed items) are tested in `tests/unit/test_utils.py`.
Future hooks import utils — duplication structurally prevented.
