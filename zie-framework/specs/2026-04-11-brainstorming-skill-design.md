---
approved: true
approved_at: 2026-04-11
backlog:
---

# Brainstorming Skill — Design Spec

**Problem:** zie-framework has no entry point for discovery. Before any backlog item exists, there is no structured way to understand the current project state, research improvement opportunities, and form requirements through discussion. Zie must manually re-state context and direction at the start of every new initiative.

**Approach:** A `zie-framework:brainstorm` skill that runs 4 phases in sequence: (A) read project knowledge artifacts to understand current state; (B) research best practices and improvement opportunities via web search scoped to the project's detected tech stack; (C) synthesize findings and present to Zie for confirmation; (D) discuss and narrow down → write `.zie/handoff.md` → ready for `/sprint`.

Intent detection: brainstorm-intent signals are added as a new pattern group in the existing `intent-sdlc.py` hook (no new hook file), so Claude receives a hint when Zie's message is exploratory.

**Core Design Principle:** Generic — works with any project using zie-framework regardless of language, domain, or structure. Deeply Claude Code-native. Extracts maximum capability from Sonnet at minimum token cost.

**Out of Scope:** This spec does not implement the `.zie/handoff.md` consumption by `/sprint` — that is covered by the conversation-capture spec. This spec only produces the artifact.

**Components:**
- `skills/brainstorm/SKILL.md` — the brainstorm skill (4 phases)
- `hooks/intent-sdlc.py` — extend with brainstorm-intent pattern group (no new hook file)
- `hooks/hooks.json` — no change needed (brainstorm patterns go into existing intent-sdlc.py)
- `.zie/handoff.md` — output artifact at `$CWD/.zie/handoff.md`; consumed by `/sprint` (see conversation-capture spec)

**`.zie/` Directory Convention:**
- Location: `$CWD/.zie/` (project root, not inside `zie-framework/`)
- Created by the first writer on first use (skill or hook creates dir if absent)
- Must be added to `.gitignore` (session ephemera — never committed)
- This is the canonical location for all session-ephemeral artifacts

**handoff.md Ownership (brainstorm vs. design-tracker):**
- `brainstorm` skill = **primary** write path: explicit brainstorm session → writes handoff.md in Phase 4 → sets `project_tmp_path("brainstorm-active", project)` flag
- `design-tracker` (conversation-capture spec) = **secondary** write path: implicit design conversations where brainstorm was NOT invoked → Stop hook checks flag → skips write if brainstorm-active is set
- Last writer does NOT win; brainstorm skill takes precedence

**Data Flow:**

*A — Phase 1: Read Project Knowledge (not source files)*
1. Discover knowledge artifacts generically: CLAUDE.md (always present), README.md, PROJECT.md/docs/ if present, package.json/pyproject.toml/go.mod (tech stack detection), git log last 20 commits
2. Extract detected tech stack: language, framework, test runner — used to scope Phase 2 searches
3. If zie-framework project detected (zie-framework/ dir present): also read ROADMAP.md, decisions/ADR-000-summary.md, backlog/
4. Freshness check: compare PROJECT.md mtime vs latest commit mtime using `is_mtime_fresh()` logic from `utils_roadmap.py`. If stale → auto-run `/resync` before proceeding. If no PROJECT.md exists → skip resync, proceed with what's available
5. Output: structured "project state snapshot" + detected tech stack, used in Phase 2 and Phase 3

*B — Phase 2: Research (≤6 queries, scoped to project)*
1. Skip search for any topic already covered by an ADR (read ADR-000-summary.md first)
2. Derive search topics from Phase 1 gaps, **scoped to detected tech stack and domain** (e.g., "Python SDLC automation best practices" not generic "SDLC best practices")
3. Run targeted searches — 4 focus areas: (i) similar tools/frameworks doing X better, (ii) best practices for AI-assisted SDLC / Claude Code patterns for this stack, (iii) solutions to specific gaps found in Phase 1, (iv) emerging Claude Code ecosystem patterns relevant to this project type
4. Hard cap: ≤6 WebSearch calls total; prefer depth over breadth

*C — Phase 3: Synthesize + Present + Confirm*
Claude presents findings in this format:
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
After presenting: Claude asks Zie "Does this look right? Shall I continue to the discussion phase?" — waits for confirmation before Phase 4.

*D — Phase 4: Discuss → Narrow → Handoff*
1. Discuss each opportunity with Zie — one at a time, ask priority + interest
2. Narrow to 1-3 items to act on
3. Create `$CWD/.zie/` dir if absent
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

## Next Step
/sprint <feature-name>
```
5. Write `project_tmp_path("brainstorm-active", project)` flag file (signals design-tracker to skip)
6. Tell Zie: "Ready — run `/sprint <feature-name>` to start the pipeline."

*intent-sdlc.py extension (brainstorm pattern group):*
Add new pattern group to existing intent-sdlc.py signal table:
- Signals: "อยากให้มี", "ควรจะ", "น่าจะเพิ่ม", "improve", "what if", "ปรับอะไรดี", "คิดว่าขาดอะไร", "research", "deep dive"
- Hint injected: `[zie-framework] intent: brainstorm — consider invoking zie-framework:brainstorm skill`
- Threshold: ≥2 matching signals (consistent with other intents)

**Error Handling:**
- intent-sdlc.py extension: inherits existing Tier 1 outer guard (bare except → exit 0)
- Phase 1 artifact missing: skip gracefully, proceed with what's found — never abort
- /resync unavailable or fails: warn to stderr, continue with stale knowledge
- Phase 2 search errors: skip failed query, continue with remaining budget
- .zie/ dir unwriteable: print handoff.md content inline instead, tell Zie to save manually
- brainstorm-active flag write fails: log warning, continue — design-tracker may double-write (acceptable)

**Testing:**
- Unit (`tests/unit/test_intent_sdlc.py`): brainstorm signals score correctly in Thai + English in extended intent-sdlc.py
- Unit: brainstorm-intent does NOT trigger on clear task descriptions ("fix bug in X", "implement Y")
- Unit: freshness check logic — stale vs fresh PROJECT.md using mtime comparison
- Unit (`tests/unit/test_brainstorm_write_handoff.py`): `write_handoff()` helper writes correct structure to temp dir
- Unit: brainstorm-active flag written after Phase 4 completes
- Integration: full brainstorm → /sprint flow (requires live session, not in CI)
