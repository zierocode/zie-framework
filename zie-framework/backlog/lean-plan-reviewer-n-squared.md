# Backlog: Replace N² pair check in plan-reviewer with O(N) file-map heuristic

**Problem:**
plan-reviewer/SKILL.md Step 10 says "For each pair of tasks, check whether they
modify any common files." For a 15-task plan that is 105 pairs. This instructs the
reviewer agent to spend significant mechanical effort on dependency checking that
could be replaced by a simpler, faster heuristic.

**Rough scope:**
- Replace "check each pair" with: "Build a file→tasks map. Flag any file appearing
  in 2+ tasks as a potential conflict." This is O(N) and catches all real conflicts.
- Update plan-reviewer SKILL.md Step 10 with the file-map heuristic
- Tests: plan-reviewer with 10-task plan detects conflict in <2 reviewer steps
