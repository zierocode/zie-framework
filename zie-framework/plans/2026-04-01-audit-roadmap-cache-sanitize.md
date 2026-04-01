---
slug: audit-roadmap-cache-sanitize
status: approved
approved: true
date: 2026-04-01
---

# Plan: Sanitize roadmap cache session_id and align with cleanup convention

## Tasks

### T1 — Fix `get_cached_roadmap`: sanitize session_id + add `tmp_dir` param

- [ ] Change signature to `def get_cached_roadmap(session_id: str, tmp_dir=None) -> str | None:`
- [ ] Add at top of function: `safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)`
- [ ] Replace `Path(f"/tmp/zie-{session_id}/roadmap.cache")` with:
  `Path(tmp_dir or tempfile.gettempdir()) / f"zie-{safe_id}" / "roadmap.cache"`
- [ ] Add `import tempfile` at top of `utils.py` if not already present

### T2 — Fix `write_roadmap_cache`: sanitize session_id + add `tmp_dir` param

- [ ] Change signature to `def write_roadmap_cache(session_id: str, content: str, tmp_dir=None) -> bool:`
- [ ] Add at top of function: `safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)`
- [ ] Replace `Path(f"/tmp/zie-{session_id}")` with:
  `Path(tmp_dir or tempfile.gettempdir()) / f"zie-{safe_id}"`

### T3 — Fix `read_roadmap_cached`: forward `tmp_dir` to both helpers

- [ ] Change signature to:
  `def read_roadmap_cached(roadmap_path: str, session_id: str, ttl: int = 30, tmp_dir=None) -> str | None:`
- [ ] Forward `tmp_dir` to both inner calls:
  - `get_cached_roadmap(session_id, tmp_dir=tmp_dir)`
  - `write_roadmap_cache(session_id, content, tmp_dir=tmp_dir)`
- [ ] All existing callers pass `tmp_dir=None` by default (backward-compatible — no call sites change)

### T4 — Extend `session-cleanup.py` to remove roadmap cache dirs

- [ ] After the existing `glob(f"zie-{safe_project}-*")` loop, add a project-scoped
  second loop that globs `zie-{safe_project}-*/roadmap.cache` within `tempfile.gettempdir()`:
  ```python
  import tempfile
  for cache_file in Path(tempfile.gettempdir()).glob(f"zie-{safe_project}*/roadmap.cache"):
      try:
          cache_file.unlink(missing_ok=True)
          parent = cache_file.parent
          if not any(parent.iterdir()):
              parent.rmdir()
      except Exception:
          pass
  ```
- [ ] Use `safe_project` (already computed via `safe_project_name()` earlier in the hook)
  to scope the glob to the current project only — avoids removing roadmap dirs from
  concurrent sessions of other projects

### T5 — Write new unit tests (AC6 path injection + AC7 cleanup)

- [ ] **T5a** — Add `test_session_id_path_injection` to `TestRoadmapCache` in
  `tests/unit/test_utils.py`:
  - Call `write_roadmap_cache("../evil", "content", tmp_dir=str(tmp_path))`
  - Assert the written file is at `tmp_path / "zie---evil" / "roadmap.cache"`
    (sanitized: `re.sub(r'[^a-zA-Z0-9_-]', '-', "../evil")` → `--evil`,
    so path is `zie--evil/roadmap.cache`)
  - Assert `(tmp_path.parent / "evil" / "roadmap.cache")` does NOT exist
    (no path traversal)
- [ ] **T5b** — Add `test_session_id_dotdot_sanitized` to `TestRoadmapCache`:
  - Assert `re.sub(r'[^a-zA-Z0-9_-]', '-', "../etc/passwd")` == `"--etc-passwd"`
  - Confirms no traversal possible
- [ ] **T5c** — Add `test_cleanup_removes_roadmap_cache_dir` to
  `tests/unit/test_session_cleanup.py::TestSessionCleanupDeletes`:
  - Generate a unique project name from `tmp_path.name`
  - Create `tempfile.gettempdir() / f"zie-{safe_project_name(project)}" / "roadmap.cache"`
  - Run hook subprocess with `CLAUDE_CWD=f"/fake/{project}"`
  - Assert the `zie-{safe_id}/` directory is gone
  - (Use real `tempfile.gettempdir()` — hook subprocess cannot be given a fake tempdir)

### T6 — Update existing `TestRoadmapCache` tests to use `tmp_dir` param

- [ ] In `tests/unit/test_utils.py::TestRoadmapCache`, pass `tmp_dir=str(tmp_path)`
  to all `write_roadmap_cache` and `read_roadmap_cached` calls so tests no longer
  write to real `/tmp/`
- [ ] Update `test_write_creates_parent_dirs` assertion from
  `Path(f"/tmp/zie-{sid}/roadmap.cache")` to `tmp_path / f"zie-{sid}" / "roadmap.cache"`

## Test Strategy

TDD order:
1. **RED** — run T5a/T5b tests → fail (no sanitization yet)
2. **GREEN** — implement T1–T3 → run T5a/T5b → pass
3. **Update** — implement T6 (retrofit existing tests with `tmp_dir`)
4. **RED** — run T5c → fail (cleanup doesn't remove roadmap dirs yet)
5. **GREEN** — implement T4 → run T5c → pass
6. **Full gate**: `make test-ci`

Verification commands at each RED/GREEN step:
```bash
pytest tests/unit/test_utils.py::TestRoadmapCache -x       # T5a/T5b + T6
pytest tests/unit/test_session_cleanup.py -x               # T5c
make test-ci                                                # full gate
```

## Rollout

1. Add `import tempfile` and `import re` to `hooks/utils.py` if not present
2. Implement T1–T3 in `hooks/utils.py` (single logical change — all backward-compatible)
3. Implement T4 in `hooks/session-cleanup.py`
4. Implement T5–T6 (tests)
5. Run `make test-ci` — gate must pass
6. Verify no callers outside `utils.py` use `write_roadmap_cache`/`get_cached_roadmap`
   directly: `grep -r "write_roadmap_cache\|get_cached_roadmap" hooks/` must show only `utils.py`
