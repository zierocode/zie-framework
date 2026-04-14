# Pattern Categories

**Purpose:** Define pattern categories used by `auto-learn` for classification.

## Categories

### 1. `workflow`

**Description:** Repeated action sequences or SDLC stage transitions.

**Examples:**
- TDD loop: test → implement → refactor
- Spec → plan → implement pipeline
- Fix → verify → release sequence
- Sprint batch processing pattern

**Detection signals:**
- Tool call sequences (Test → Write → Bash)
- ROADMAP lane transitions
- Repeated command invocations

### 2. `code`

**Description:** Code style, structure, or organization patterns.

**Examples:**
- Naming conventions (snake_case, PascalCase)
- File organization patterns
- Function/method structure
- Test organization patterns
- Import organization

**Detection signals:**
- Repeated code structures
- Consistent naming across files
- File/directory patterns

### 3. `decision`

**Description:** Recurring decision patterns or architecture choices.

**Examples:**
- Tool/library selection (pytest vs unittest)
- Architecture decisions
- Dependency choices
- API design decisions

**Detection signals:**
- Explicit decision statements
- Comparison/evaluation patterns
- "Chose X over Y" statements

### 4. `communication`

**Description:** Interaction patterns between user and Claude.

**Examples:**
- Clarification question types
- User preference patterns
- Feedback incorporation patterns
- Approval/rejection patterns

**Detection signals:**
- Question/answer sequences
- User correction patterns
- Preference statements

## Confidence Scoring

Each pattern receives a confidence score (0.0-1.0) based on:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Frequency | 0.4 | `occurrences / max_occurrences` |
| Consistency | 0.3 | `1 - (variance / mean)` |
| Recency | 0.3 | `exp(-days_since / 30)` |

**Thresholds:**
- `>= 0.95` → `auto_apply: true` (candidate for `auto-improve`)
- `>= 0.80` → high confidence (surface to user)
- `< 0.80` → low confidence (log only)

## Pattern ID Format

```
{category}-{YYYYMMDD}-{NNN}
```

Example: `workflow-20260414-001`
