---
slug: audit-hook-refactor
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-hook-refactor.md
---

# Spec: Hook Refactor — Shared Utils + /tmp Isolation

## Problem

Three hooks (session-learn.py, wip-checkpoint.py, session-resume.py) contain ~40 LOC of identical ROADMAP "Now" section parsing, copy-pasted across files — any format change requires touching all three. Two hooks use hardcoded global `/tmp` paths (`/tmp/zie-framework-last-test`, `/tmp/zie-framework-edit-count`), causing cross-project debounce interference and merged edit counters when multiple Claude Code sessions run simultaneously on different projects. Eleven bare `except Exception: pass` statements across five hooks swallow all errors silently, making failures invisible during development and debugging.

## Approach

Create `hooks/utils.py` as a non-hook shared library with two functions: `parse_roadmap_now(roadmap_path)` returns the cleaned list of "Now" items from a ROADMAP.md, and `project_tmp_path(name, project)` returns a `Path` of the form `/tmp/zie-{safe_project}-{name}` where `safe_project` is the project name with non-alphanumeric characters replaced by hyphens. All three ROADMAP-parsing hooks import and call `parse_roadmap_now` instead of duplicating the loop. All `/tmp/zie-framework-*` references are replaced with `project_tmp_path(...)` calls using the project name derived from `cwd.name`. Bare `except Exception: pass` blocks at the JSON parse boundary (top of each hook) remain silent and are annotated `# intentional — malformed event must not crash hook`; all other caught exceptions write a single diagnostic line to `sys.stderr` so failures surface in Claude Code's hook log without crashing the hook. A Stop hook entry in `hooks.json` calls a cleanup script that removes all `/tmp/zie-{project}-*` files on session end. Regex patterns in `intent-detect.py` are compiled once at module level into a `COMPILED_PATTERNS` dict, eliminating per-prompt recompilation. `session-resume.py` truncates the ROADMAP read to the first 100 lines when the file exceeds 200 lines, keeping SessionStart latency low.

## Acceptance Criteria

- [ ] AC-1: `hooks/utils.py` exists and exports `parse_roadmap_now(roadmap_path: Path) -> list[str]` and `project_tmp_path(name: str, project: str) -> Path`; both are covered by `tests/unit/test_utils.py` with cases for missing header, empty Now section, and markdown link stripping.
- [ ] AC-2: `session-learn.py`, `wip-checkpoint.py`, and `session-resume.py` each import from `utils` and contain zero inline ROADMAP parsing loops — the duplicated `in_now` block is fully removed from all three.
- [ ] AC-3: `auto-test.py` references `/tmp/zie-{project}-last-test` via `project_tmp_path()`; `wip-checkpoint.py` references `/tmp/zie-{project}-edit-count` via `project_tmp_path()` — no hook contains a hardcoded `/tmp/zie-framework-*` literal.
- [ ] AC-4: All `except Exception: pass` blocks that guard inner logic (not the top-level JSON parse) are replaced with `except Exception as e: print(f"[zie-framework] {hook_name}: {e}", file=sys.stderr)`.
- [ ] AC-5: The top-level JSON parse guards retain silent failure but carry the comment `# intentional — malformed event must not crash hook`.
- [ ] AC-6: `hooks.json` includes a Stop hook entry pointing to a `hooks/session-cleanup.py` script that deletes all `/tmp/zie-{project}-*` temp files for the current session's project.
- [ ] AC-7: The dead `pass` block at `auto-test.py` lines 53-56 (inside the test-file skip branch) is removed; the surrounding `if` branch either contains meaningful logic or is deleted entirely.
- [ ] AC-8: `import re` is moved to the top-level import block in both `session-learn.py` and `session-resume.py` — no `import re` appears inside a function body or loop.
- [ ] AC-9: `hooks/hooks.json` (or an inline comment block) documents the hook output protocol: Stop/SessionStart hooks print plain text; UserPromptSubmit hooks print a JSON object with `additionalContext`; PostToolUse hooks print plain text warnings.
- [ ] AC-10: `intent-detect.py` defines `COMPILED_PATTERNS` at module level as `{category: [re.compile(p) for p in patterns] for category, patterns in PATTERNS.items()}` and the scoring loop uses `COMPILED_PATTERNS` instead of calling `re.search(pattern, message)` with raw strings.
- [ ] AC-11: `session-resume.py` reads ROADMAP.md and, when `len(lines) > 200`, uses only `lines[:100]` for section parsing — verified by a unit test that passes a 250-line synthetic ROADMAP and asserts only the first 100 lines are processed.
- [ ] AC-12: All existing hook unit tests continue to pass (`make test-unit` green) after the refactor.

## Out of Scope

- Changes to command files (`commands/zie-*.md`) or skill files (`skills/`)
- Modifying the ROADMAP.md format or section naming conventions
- Changing zie-memory API call logic, endpoints, or authentication
- Adding new hook events beyond the Stop cleanup entry
- Altering `session-resume.py`'s output format or the context it injects
- Performance profiling or benchmarking of hook execution time
- Python version compatibility below 3.9

## Files Changed

| File | Action |
|---|---|
| `hooks/utils.py` | Create — shared library with `parse_roadmap_now` and `project_tmp_path` |
| `hooks/session-cleanup.py` | Create — Stop hook that removes project-scoped /tmp files |
| `hooks/session-learn.py` | Modify — import utils, remove inline ROADMAP loop, move `import re`, stderr logging |
| `hooks/wip-checkpoint.py` | Modify — import utils, remove inline ROADMAP loop, replace /tmp path, stderr logging |
| `hooks/session-resume.py` | Modify — import utils, replace ROADMAP loop, move `import re`, add 200-line truncation |
| `hooks/auto-test.py` | Modify — replace /tmp path via `project_tmp_path`, remove dead pass block lines 53-56 |
| `hooks/intent-detect.py` | Modify — pre-compile PATTERNS into COMPILED_PATTERNS at module level |
| `hooks/hooks.json` | Modify — add Stop hook entry for session-cleanup.py, add output protocol comment block |
| `tests/unit/test_utils.py` | Create — unit tests for `parse_roadmap_now` and `project_tmp_path` |
