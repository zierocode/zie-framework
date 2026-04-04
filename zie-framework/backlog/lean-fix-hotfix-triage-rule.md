# Backlog: Add single-sentence triage rule to /fix and /hotfix descriptions

**Problem:**
/fix and /hotfix have overlapping descriptions with no clear decision rule:
- /fix: "Fast path for fixing bugs. Skips brainstorming and planning."
- /hotfix: "Emergency fix track that cannot wait for the full pipeline."
Both skip spec/plan. Both write regression tests. The practical difference (drift log
entry + immediate release) is buried in step details. Users will guess wrong.

**Rough scope:**
- Add to /fix description: "Use for non-urgent bugs. Does not trigger an immediate release."
- Add to /hotfix description: "Use only for prod incidents requiring immediate release.
  Triggers release gate automatically. For non-urgent bugs, use /fix instead."
- Mirror the same distinction in PROJECT.md Commands table description column
- Tests: no test needed (doc-only change)
