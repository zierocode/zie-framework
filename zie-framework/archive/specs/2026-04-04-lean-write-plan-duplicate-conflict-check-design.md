---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-write-plan-duplicate-conflict-check.md
---

# lean-write-plan-duplicate-conflict-check — Design Spec

**Problem:** `skills/write-plan/SKILL.md` contains an identical "File conflict check" rule stated word-for-word twice — once under "Task Sizing Guidance" (line 84) and again under "โครงสร้าง Task" (lines 119–121) — wasting ~150 tokens per skill invocation with zero added value.

**Approach:** Remove the shorter, less-detailed first instance (line 84, under "Task Sizing Guidance"). The second instance (lines 119–121, under "โครงสร้าง Task") is the canonical location — it appears immediately before the `depends_on` serialization mechanism and includes the actionable resolution (`add <!-- depends_on: TN --> to serialize them`), making it the more useful and contextually placed instance. Add a pytest structural test that scans all `skills/*/SKILL.md` files for verbatim duplicate paragraph blocks to prevent regressions.

**Components:**
- `skills/write-plan/SKILL.md` — remove duplicate paragraph at lines 84–85
- `tests/unit/test_skill_dedup.py` — new structural test asserting no duplicate paragraph blocks exist in any skill file

**Data Flow:**
1. Read `skills/write-plan/SKILL.md`
2. Identify the two identical "File conflict check" paragraphs
3. Delete the first instance (under "Task Sizing Guidance" section, line 84)
4. Verify the remaining instance at lines 119–121 is intact and contextually correct
5. Write `tests/unit/test_skill_dedup.py` — iterates all `skills/*/SKILL.md`, splits content into non-empty paragraph blocks, asserts no paragraph appears ≥2 times verbatim
6. Run `make test-unit` — structural test must pass

**Edge Cases:**
- The structural test must ignore YAML frontmatter (lines before the first `---` closing fence) to avoid false positives on metadata fields
- Short one-line paragraphs (e.g. "---" horizontal rules, blank structural lines) must be excluded from dedup checks to avoid false positives
- The test must only flag verbatim duplicates — near-duplicates or paraphrases are out of scope

**Out of Scope:**
- Near-duplicate or paraphrased guidance across sections
- Deduplication across different skill files (inter-skill duplicates)
- Refactoring or rewording the remaining "File conflict check" paragraph
- Any changes to other skill files
