# Plan: intent-sdlc — Gate ROADMAP Read for Non-Now-Dependent Intents

status: approved

## Tasks

### 1. Define `NOW_DEPENDENT_INTENTS` constant

In `hooks/intent-sdlc.py`, add after the `SUGGESTIONS` dict (near line 93):

```python
NOW_DEPENDENT_INTENTS = frozenset({"plan", "implement", "status"})
```

---

### 2. Gate `read_roadmap_cached()` and Now-lane parse

Replace the unconditional block (lines 298–310):

```python
# ── SDLC context (reads ROADMAP once via cache) ───────────────────────────
roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
roadmap_content = read_roadmap_cached(roadmap_path, session_id)
now_items = parse_roadmap_section_content(roadmap_content, "now")
```

With the gated version:

```python
# ── SDLC context (reads ROADMAP only for Now-dependent intents) ──────────
roadmap_path = cwd / "zie-framework" / "ROADMAP.md"
roadmap_content = ""
now_items: list = []
if best in NOW_DEPENDENT_INTENTS or intent_cmd is None:
    roadmap_content = read_roadmap_cached(roadmap_path, session_id)
    now_items = parse_roadmap_section_content(roadmap_content, "now")
```

The `intent_cmd is None` branch preserves `_positional_guidance` for no-dominant-intent prompts that mention a known slug.

---

### 3. Add tests for non-Now intents in `TestIntentSdlcRoadmapCache`

Add a new test class or extend the existing `TestIntentSdlcRoadmapCache` with:

- `test_backlog_intent_no_roadmap_read` — use `backlog` intent prompt, assert output is produced and `task:none` appears (or `stage:idle`). Verify no `⛔`.
- `test_spec_intent_no_roadmap_read` — same for `spec` intent.
- `test_fix_intent_no_roadmap_read` — same for `fix` intent.
- `test_release_intent_no_roadmap_read` — same for `release` intent.

All four tests: provide a ROADMAP with an active Now item and assert the non-Now intent context does NOT include the active task name (confirming the read was skipped).

---

### 4. Verify no regression

Run:

```bash
make test-fast
```

All existing `TestPipelineGates`, `TestPositionalGuidance`, `TestIntentSdlcRoadmapCache`, and `TestIntentSdlcHappyPath` must pass unchanged.

---

## Files to Change

| File | Change |
| --- | --- |
| `hooks/intent-sdlc.py` | Add `NOW_DEPENDENT_INTENTS` constant; gate `read_roadmap_cached()` + `parse_roadmap_section_content()` call |
| `tests/unit/test_hooks_intent_sdlc.py` | Add 4 new test cases asserting non-Now intents skip ROADMAP read |
