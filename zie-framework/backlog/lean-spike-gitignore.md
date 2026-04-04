# Backlog: Add .gitignore guidance for spike directories in /spike command

**Problem:**
/spike Step 1 creates `spike-<slug>/` at repo root with no guidance to add it
to .gitignore. Spike directories are exploratory artifacts (throwaway code,
experiments) and should not be committed. /init creates `zie-framework/evidence/`
with a gitignore entry — the same pattern should apply here.

**Rough scope:**
- Add step in /spike: after creating spike-<slug>/, run `echo "spike-*/" >> .gitignore`
  or check if already gitignored
- Add note: "spike directories are throwaway — delete when done or archive to
  zie-framework/archive/ if findings are worth keeping"
- Tests: structural test asserting spike command includes gitignore step
