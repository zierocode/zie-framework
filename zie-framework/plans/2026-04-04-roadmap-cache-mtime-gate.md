# Plan: Replace ROADMAP Cache TTL with mtime-Gate

**status:** approved
**slug:** roadmap-cache-mtime-gate
**spec:** zie-framework/specs/2026-04-04-roadmap-cache-mtime-gate-design.md
**date:** 2026-04-04

---

## Tasks

### Task 1 — Update `write_roadmap_cache` in `utils_roadmap.py`

Change the cache file name from `roadmap.cache` (plain text) to `roadmap-cache.json` (JSON).
Write `{"mtime": <float>, "content": "<str>"}` where `mtime` is `os.path.getmtime(roadmap_path)`.

Signature change:
```python
# before
def write_roadmap_cache(session_id: str, content: str, tmp_dir=None) -> None:

# after
def write_roadmap_cache(session_id: str, content: str, roadmap_path, tmp_dir=None) -> None:
```

- Read `os.path.getmtime(roadmap_path)` inside the function (wrap in `try/except`).
- Write JSON payload via `json.dumps({"mtime": mtime, "content": content})`.
- Use direct `.write_text()` (consistent with existing pattern; `safe_write_tmp` not needed here).

---

### Task 2 — Update `get_cached_roadmap` in `utils_roadmap.py`

Replace TTL check with mtime comparison.

Signature change:
```python
# before
def get_cached_roadmap(session_id: str, ttl: int = 30, tmp_dir=None) -> str | None:

# after
def get_cached_roadmap(session_id: str, roadmap_path, tmp_dir=None) -> str | None:
```

- Cache file: `roadmap-cache.json` (JSON, not plain text).
- Load JSON; compare `abs(data["mtime"] - os.path.getmtime(roadmap_path)) > 0.001` → return `None` on mismatch.
- Return `data["content"]` on hit.
- Wrap entire body in `try/except Exception: return None`.

---

### Task 3 — Update `read_roadmap_cached` in `utils_roadmap.py`

Remove `ttl` parameter; pass `roadmap_path` through to both inner functions.

Signature change:
```python
# before
def read_roadmap_cached(roadmap_path, session_id: str, ttl: int = 30, tmp_dir=None) -> str:

# after
def read_roadmap_cached(roadmap_path, session_id: str, tmp_dir=None) -> str:
```

- Call `get_cached_roadmap(session_id, roadmap_path, tmp_dir=tmp_dir)`.
- Call `write_roadmap_cache(session_id, content, roadmap_path, tmp_dir=tmp_dir)` on miss.

---

### Task 4 — Remove `import time` from `utils_roadmap.py`

Confirm no remaining usages of `time` in the file after Task 1-3, then delete the import line.

---

### Task 5 — Update callers (no signature break needed, `ttl` was keyword-only default)

All four callers already call `read_roadmap_cached(roadmap_path, session_id)` without passing `ttl` explicitly — no caller changes required. Verify with grep after editing.

Files to verify (no edit expected):
- `hooks/sdlc-compact.py`
- `hooks/subagent-context.py`
- `hooks/failure-context.py`
- `hooks/intent-sdlc.py`

---

### Task 6 — Write unit tests

File: `tests/unit/test_utils_roadmap_cache_mtime.py`

Test cases (use `tmp_path` fixture):
1. **cache hit** — write cache with correct mtime, `get_cached_roadmap` returns content.
2. **cache miss on mtime change** — write cache, then touch ROADMAP.md (update mtime), assert `None`.
3. **cache miss on no file** — no cache file exists, assert `None`.
4. **write round-trip** — `write_roadmap_cache` + `get_cached_roadmap` returns original content.
5. **read_roadmap_cached hit** — cache warm, no disk read of roadmap file after first call.
6. **read_roadmap_cached miss → reads disk** — cold cache, returns file content and warms cache.
7. **read_roadmap_cached missing roadmap file** — ROADMAP.md absent, returns `""`.

---

### Task 7 — Run tests and lint

```bash
make lint
make test-fast
```

Fix any failures before marking done.

---

## Files to Change

| File | Change |
| ---- | ------ |
| `hooks/utils_roadmap.py` | Tasks 1-4: update `write_roadmap_cache`, `get_cached_roadmap`, `read_roadmap_cached`; remove `import time` |
| `tests/unit/test_utils_roadmap_cache_mtime.py` | Task 6: new test file (7 test cases) |

## Files to Verify (read-only)

| File | Why |
| ---- | --- |
| `hooks/sdlc-compact.py` | Caller — confirm no `ttl` arg passed |
| `hooks/subagent-context.py` | Caller — confirm no `ttl` arg passed |
| `hooks/failure-context.py` | Caller — confirm no `ttl` arg passed |
| `hooks/intent-sdlc.py` | Caller — confirm no `ttl` arg passed |
