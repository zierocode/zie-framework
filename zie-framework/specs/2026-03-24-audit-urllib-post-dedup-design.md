---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-urllib-post-dedup.md
---

# Shared urllib POST Helper for zie-memory API — Design Spec

**Problem:** `session-learn.py` (lines 48-65) and `wip-checkpoint.py` (lines 62-82) each contain an independent implementation of JSON + Bearer token HTTP POST via `urllib.request`, duplicating ~35 lines of structurally identical code that will inevitably diverge on headers, timeouts, or error handling.

**Approach:** Extract a `call_zie_memory_api(url: str, key: str, endpoint: str, payload: dict, timeout: int = 5) -> None` helper into `utils.py`. Both callers replace their inline `urllib.request` blocks with a single call to this helper. The helper raises on HTTP errors (non-2xx) so callers can decide whether to log; it does not swallow exceptions.

**Components:**
- `hooks/utils.py` — add `call_zie_memory_api()` helper (~12 lines)
- `hooks/session-learn.py` — replace lines 48-65 with `call_zie_memory_api(...)` call inside existing try/except
- `hooks/wip-checkpoint.py` — replace lines 62-82 with `call_zie_memory_api(...)` call inside existing try/except

**Data Flow:**
1. Caller builds `payload` dict (unchanged)
2. Calls `call_zie_memory_api(api_url, api_key, "/api/hooks/<endpoint>", payload, timeout=N)`
3. Helper encodes payload as JSON, sets `Authorization: Bearer` + `Content-Type: application/json` headers
4. Calls `urllib.request.urlopen(req, timeout=timeout)`
5. On any exception, helper re-raises — caller's existing `except Exception as e: print(...)` handles logging

**Edge Cases:**
- `api_url` does not end with `/` — helper constructs `f"{api_url}{endpoint}"` so endpoint must include leading `/`; both current callers already use absolute paths
- Non-2xx HTTP response — `urllib.request.urlopen` raises `urllib.error.HTTPError`; bubbles to caller's except block
- `payload` contains non-serializable values — `json.dumps()` raises `TypeError` before any network call; caller's except catches it
- Timeout differences — `session-learn.py` uses 5s, `wip-checkpoint.py` uses 3s; each caller passes its own value so no behavior change

**Out of Scope:**
- Switching from `urllib.request` to `requests` or `httpx`
- Retry logic or exponential backoff
- Response body parsing (current callers discard response body)
