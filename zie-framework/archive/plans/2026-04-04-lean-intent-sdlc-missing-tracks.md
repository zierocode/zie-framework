---
slug: lean-intent-sdlc-missing-tracks
date: 2026-04-04
approved: true
approved_at: 2026-04-04
model: sonnet
effort: low
---

# Plan: lean-intent-sdlc-missing-tracks

## Goal

Extend `hooks/intent-sdlc.py` `PATTERNS` and `SUGGESTIONS` with three new categories — `hotfix`, `chore`, `spike`. Add tests covering the new detection paths.

## Tasks

### Task 1 — Update `hooks/intent-sdlc.py`

**File:** `hooks/intent-sdlc.py`

Add to `PATTERNS` dict:

```python
"hotfix": [
    r"\bhotfix\b",
    r"\bemergency\s+fix\b",
    r"\bprod(?:uction)?\s+(?:down|broken|issue)\b",
    r"\bcannot\s+wait\b",
    r"\bblocking\s+(?:prod|release)\b",
],
"chore": [
    r"\bchore\b",
    r"\bupdate\s+deps(?:endencies)?\b",
    r"\bbump\s+version\b",
    r"\bclean\s+up\b",
    r"\brefactor\b",
    r"\bupdate\s+docs\b",
],
"spike": [
    r"\bspike\b",
    r"\bexplore\s+(?:this|the|an?)\b",
    r"\bproof\s+of\s+concept\b",
    r"\bpoc\b",
    r"\binvestigate\b",
    r"\bresearch\b",
],
```

Add to `SUGGESTIONS` dict:

```python
"hotfix": "/hotfix",
"chore": "/chore",
"spike": "/spike",
```

Extend `no_track_msg` condition to include new intents:

```python
if best in ("implement", "fix", "hotfix", "chore", "spike") and not now_task:
    # existing no_track_msg logic
```

### Task 2 — Add tests

**File:** `tests/unit/test_hooks_intent_sdlc.py`

Add `TestNewIntentDetection` class:

```python
class TestNewIntentDetection:
    def test_hotfix_detected(self):
        # "emergency fix for prod" → hotfix
        result = detect_intent("emergency fix for prod")
        assert result["intent"] == "hotfix"
        assert result["cmd"] == "/hotfix"

    def test_spike_detected(self):
        # "let's explore this idea" → spike
        result = detect_intent("let's explore this idea")
        assert result["intent"] == "spike"
        assert result["cmd"] == "/spike"

    def test_chore_detected(self):
        # "update deps" → chore
        result = detect_intent("update deps for the project")
        assert result["intent"] == "chore"
        assert result["cmd"] == "/chore"

    def test_hotfix_no_overlap_with_fix(self):
        # "hotfix" should not match fix category
        result = detect_intent("hotfix the auth bug")
        assert result["intent"] == "hotfix"
```

(Adjust `detect_intent` call signature to match actual test helper in the file.)

### Task 3 — Run tests

```bash
make test-unit
```

## Acceptance Criteria

- `PATTERNS` dict has `hotfix`, `chore`, `spike` keys with keyword lists
- `SUGGESTIONS` dict maps them to `/hotfix`, `/chore`, `/spike`
- `no_track_msg` fires for new intents when Now lane is empty
- Pattern word-boundary anchors prevent "hotfix" matching "fix" category
- Tests cover hotfix, spike, chore detection; all pass
