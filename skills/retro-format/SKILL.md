---
name: retro-format
description: Retrospective format and ADR structure for /zie-retro
user-invocable: false
argument-hint: ""
model: haiku
effort: low
context: fork
---

# Retro Format — zie-framework

## Input

`$ARGUMENTS` (optional compact JSON bundle from `/zie-retro`):

```json
{
  "shipped": ["feat: foo", "fix: bar"],
  "commits_since_tag": 5,
  "pain_points": [],
  "decisions": [],
  "roadmap_done_tail": "- [x] Previous feature — v1.0.0 2026-01-01"
}
```

If `$ARGUMENTS` is empty or unparseable: generate all sections using whatever
context is available. All five retro sections must still be produced.

## โครงสร้าง Retrospective

Generate a retrospective with these sections. Keep each section concise — bullet
points, not prose.

### สิ่งที่ Ship ออกไป

List every feature, fix, or improvement that was completed. Include version if
released.

### สิ่งที่ทำงานได้ดี

Patterns, approaches, tools that saved time or reduced friction.
Only note things worth repeating — skip obvious basics.

### สิ่งที่เจ็บปวด (Pain Points)

Friction points, unexpected complexity, things that slowed down.
Be specific — vague "communication" complaints are useless.

### การตัดสินใจสำคัญ

Decisions with lasting consequences — candidates for ADRs.
Each decision: what → why → consequence.

### Pattern ที่ควรจำ

Reusable techniques worth storing in the brain as P1/P2 memories.

## รูปแบบ ADR

Only write an ADR when the decision:

1. Has lasting consequences (will affect future work)
2. Was non-obvious (could have gone a different way)
3. Someone might question later

**Template** (`zie-framework/decisions/ADR-NNN-slug.md`):

```markdown
# ADR-NNN: <Title — what was decided>

Date: YYYY-MM-DD
Status: Accepted

## Context
<1-3 sentences: what situation made this decision necessary>

## Decision
<1-3 sentences: exactly what was decided>

## Consequences
**Positive:** <what this enables or makes easier>
**Negative:** <what this makes harder or trades off>
**Neutral:** <things that change but are neither better nor worse>
```

**What does NOT need an ADR:**

- Routine implementation choices (which variable name, which loop style)
- Things that are easily reversible
- Library version choices (unless the version has breaking changes)
- Performance micro-optimizations

## ความถี่ของ Retro

| Trigger | Depth |
| --- | --- |
| After /zie-release | Full retro + ADRs |
| After a major debugging session | Patterns only (no full retro) |
| End of long session (3+ hours) | Brief "what worked/what was painful" |
| Weekly (even without a release) | Light review of ROADMAP + brain |

## Checklist อัปเดต ROADMAP

After every retro, review ROADMAP.md:

- [ ] All shipped items moved to Done with date + version
- [ ] Next section re-prioritized based on learnings
- [ ] Any Icebox items that became relevant moved to Next
- [ ] New items discovered during the session added
- [ ] Remove items that are no longer relevant

## Compaction Check

After updating the ROADMAP Done section, run compaction:

```python
import sys
from pathlib import Path

roadmap_path = Path("zie-framework/ROADMAP.md")
if not roadmap_path.exists():
    print("[zie-framework] retro-format: ROADMAP.md not found, skip compaction", file=sys.stderr)
else:
    sys.path.insert(0, str(Path("hooks")))
    from utils import compact_roadmap_done
    was_compacted, old_count, version_range = compact_roadmap_done(str(roadmap_path))
    if was_compacted:
        print(f"Compacted {old_count} old entries ({version_range.replace('-', '\u2013')}) into archive. Keep 20 recent entries in ROADMAP. {old_count} features shipped.")
    else:
        print("Done section has only recent entries, no archival needed")
```
