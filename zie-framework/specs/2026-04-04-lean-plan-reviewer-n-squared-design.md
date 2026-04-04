---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-plan-reviewer-n-squared.md
---

# Lean Plan-Reviewer N² → O(N) File-Map — Design Spec

**Problem:** plan-reviewer Step 10 instructs the reviewer to check every pair of tasks for shared file dependencies. For a 15-task plan this is 105 pairs — quadratic mechanical effort that scales poorly and is unnecessary.

**Approach:** Replace the "check each pair" instruction with an O(N) file-map heuristic: scan each task once to extract file paths, build a `file → [task IDs]` map, then flag any file appearing in 2+ task entries as a potential conflict. This catches every real conflict in a single linear pass.

**Components:**
- `skills/plan-reviewer/SKILL.md` — Step 10 rewritten with file-map algorithm

**Data Flow:**
1. Reviewer reads the task list from the plan file
2. For each task, extract all file paths mentioned (creates, modifies, references)
3. Build map: `file → list of task IDs`
4. For each file with 2+ task IDs: if no `depends_on` annotation connects those tasks → blocking issue
5. For each task with no shared files and no `depends_on`: advisory suggestion to add parallel-execution annotation

**Edge Cases:**
- 0 or 1 tasks → map is empty, no conflicts possible, skip check entirely
- File mentioned only once → no flag
- File flagged but tasks already have correct `depends_on` → not a conflict, skip
- File references extracted from narrative prose by pattern match → false negatives acceptable; heuristic, not exhaustive parse

**Out of Scope:**
- No changes to spec-reviewer, impl-reviewer, write-plan, or any other skill
- No programmatic/automated parsing — reviewer applies the heuristic mentally while reading the plan
- No change to the advisory wording for independent tasks (only the detection algorithm changes)
