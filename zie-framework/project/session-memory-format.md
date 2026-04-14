# Session Memory Format

**Purpose:** Schema for session memory files stored in `.zie/memory/session-*.json`. Used by `auto-learn` (write) and `auto-inject` (read).

## File Location

```
.zie/memory/session-YYYYMMDD-HHMMSS.json
```

Files are append-only. Latest session symlinked to `.zie/memory/latest.json`.

## JSON Schema

```json
{
  "session_id": "20260414-093000",
  "timestamp": {
    "start": "2026-04-14T09:30:00Z",
    "end": "2026-04-14T10:45:00Z"
  },
  "duration_seconds": 4500,
  "summary": "Auto-generated session summary (1-2 sentences)",
  "statistics": {
    "tool_calls": 42,
    "files_modified": 5,
    "tests_run": 12,
    "commits": 2,
    "lines_added": 150,
    "lines_deleted": 30
  },
  "patterns": [
    {
      "id": "pattern-001",
      "category": "workflow",
      "description": "TDD loop: test → implement → refactor",
      "confidence": 0.97,
      "evidence": ["test-unit run before implement", "refactor after green"],
      "frequency": 5,
      "auto_apply": true
    }
  ],
  "decisions": [
    {
      "id": "decision-001",
      "description": "Chose pytest over unittest",
      "rationale": "Better fixture support",
      "adr_suggested": false
    }
  ],
  "context_keywords": ["tdd", "pytest", "hooks"],
  "active_feature": "auto-learn",
  "sdlc_stage": "implement"
}
```

## Field Definitions

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | `YYYYMMDD-HHMMSS` format |
| `timestamp.start` | ISO 8601 | Session start time |
| `timestamp.end` | ISO 8601 | Session end time |
| `summary` | string | 1-2 sentence summary |
| `patterns` | array | Extracted patterns (may be empty) |
| `context_keywords` | array | Top 5 keywords from session |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `duration_seconds` | number | — | Session duration |
| `statistics` | object | — | Tool usage stats |
| `decisions` | array | [] | Decisions made |
| `active_feature` | string | — | Now lane feature |
| `sdlc_stage` | string | "idle" | Current SDLC stage |

## Pattern Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | `pattern-NNN` |
| `category` | string | See pattern-categories.md |
| `description` | string | Pattern description |
| `confidence` | number | 0.0-1.0 |
| `evidence` | array | Supporting evidence |
| `frequency` | number | Occurrences in session |
| `auto_apply` | boolean | `confidence >= 0.95` |

## Storage Rules

1. **Append-only** — never modify existing session files
2. **Permissions** — `0o600` (user read/write only)
3. **Rotation** — sessions >90 days archived automatically
4. **Symlink** — `latest.json` points to most recent session
