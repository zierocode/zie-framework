---
name: brainstorm
description: Discovery skill — read project context, research best practices, synthesize opportunities, discuss with Zie, write .zie/handoff.md ready for /sprint.
user-invocable: true
context: fork
agent: general-purpose
allowed-tools: Read, Grep, Glob, WebSearch, Bash, Write
argument-hint: "[topic]"
model: sonnet
effort: medium
---

# zie-framework:brainstorm — Discovery & Handoff

Entry point skill for all new work. Run before /sprint or /backlog to understand project state, research improvements, and form requirements through discussion. Runs 4 phases in sequence. Generic — works with any project.

---

## Context Bundle

<!-- context-load: adrs + project context -->
Extract keywords from brainstorm topic (split on whitespace, remove stop words, take top 6 unique terms).
Invoke `Skill(zie-framework:load-context, '<keywords>')` → result available as `context_bundle`. Use `context_bundle` in place of direct ADR/context.md reads below.

## Phase 1 — Read Project Knowledge (not source files)

1. Discover knowledge artifacts generically: `CLAUDE.md` (always read first), `README.md` (if present), `PROJECT.md`/`docs/` (if present), `package.json`/`pyproject.toml`/`go.mod` (detect tech stack), `git log --oneline -20` (recent activity).
2. Detect tech stack: language, framework, test runner — scopes Phase 2.
3. If `zie-framework/` dir present: read `ROADMAP.md`, use `context_bundle` for ADR summary + project context, list `backlog/` items.
4. Freshness check: compare `PROJECT.md` mtime vs latest commit mtime via `is_mtime_fresh(max_mtime=git_commit_mtime, written_at=project_md_mtime)`. Stale → auto-run `/resync`. No `PROJECT.md` → skip check.
5. Output: structured "project state snapshot" + detected tech stack.

---

## Phase 2 — Research (≤6 queries, scoped to project)

1. Check `context_bundle` for ADR decisions — skip already-decided topics.
2. Derive search topics from Phase 1 gaps, **scoped to detected tech stack** (e.g. "Python SDLC automation best practices" not "SDLC best practices").
3. Run 4 focus areas: similar tools doing X better, AI-assisted SDLC patterns for this stack, solutions to Phase 1 gaps, emerging Claude Code ecosystem patterns.
4. Hard cap: ≤6 WebSearch calls total. Prefer depth over breadth.

---

## Phase 3 — Synthesize + Present + Confirm

Present findings in this format:

```
## Project Health
<gaps, pain points, strengths from Phase 1>

## Improvement Opportunities
1. [High impact] ...
2. [Medium impact] ...
3. [Quick win] ...

## Research Insights
- Pattern X from tool Y — applicable because Z (scoped to <detected stack>)
- Best practice W — currently missing in this project
```

Ask Zie: > "Does this look right? Shall I continue to the discussion phase?" Wait for confirmation before Phase 4.

---

## Phase 4 — Discuss → Narrow → Handoff

1. Discuss each opportunity with Zie — one at a time, ask priority + interest.
2. Narrow to 1-3 items to act on.
3. Create `$CWD/.zie/` dir if absent (`mkdir -p`).
4. Write `$CWD/.zie/handoff.md`:

```markdown
---
captured_at: YYYY-MM-DDTHH:MM:SSZ
feature: <name>
source: brainstorm
---

## Goals
- <bullet per goal>

## Key Decisions
- <bullet per decision made in discussion>

## Constraints
- <bullet per constraint>

## Open Questions
- <bullet per unresolved question>

## Context Refs
- <file paths or commands mentioned as relevant>

## Next Step
/sprint <feature-name>
```

5. Write `project_tmp_path("brainstorm-active", project)` flag file:
   - `project` = current working directory name (from `$CLAUDE_CWD` or `os.getcwd()`)
   - Path: `Path(tempfile.gettempdir()) / f"zie-{re.sub(r'[^a-zA-Z0-9]', '-', project)}-brainstorm-active"`
   - Content: `"active"` — signals `stop-capture.py` (conversation-capture spec) to skip its write.
6. Tell Zie: "Ready — run `/sprint <feature-name>` to start the pipeline."

---

## Error Handling

| Error | Response |
| --- | --- |
| Phase 1 artifact missing | Skip gracefully, proceed with what's found |
| `/resync` unavailable | Warn to stderr, continue with stale knowledge |
| Phase 2 search errors | Skip failed query, continue with remaining budget |
| `.zie/` dir unwriteable | Print handoff.md inline, tell Zie to save manually |
| `brainstorm-active` flag write fails | Log warning, continue — design-tracker may double-write (acceptable) |
