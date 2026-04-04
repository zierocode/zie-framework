# Backlog: Remove duplicate file conflict check in write-plan SKILL.md

**Problem:**
write-plan/SKILL.md has identical "File conflict check" guidance in two separate
sections (lines 84–85 and lines 119–121). The same rule ("Before assigning tasks,
verify no two independent tasks write to the same output file") is stated word-for-
word twice. ~150 tokens of pure duplication.

**Rough scope:**
- Remove one of the two identical instances
- Verify the remaining instance is in the more prominent/useful location
- Tests: structural test asserting no duplicate paragraph blocks in skill files
