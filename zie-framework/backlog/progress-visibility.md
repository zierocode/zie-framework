# Progress Visibility for Long-Running Commands

## Problem

Long-running commands give no feedback about where they are or how much
remains. `/zie-audit` can run 3–8 minutes across 5 phases and 15 web
searches with no intermediate output. `/zie-release` runs 7+ gates
sequentially with no numbering. The user has no way to know if Claude is
halfway done or just starting, or whether a specific phase failed early.

## Motivation

Visibility into progress reduces uncertainty and allows the user to context-
switch confidently ("this will take a few minutes") rather than sitting and
watching. Each command has a natural phase or step structure — surfacing that
structure as output costs nothing but makes long sessions significantly less
opaque.

## Rough Scope

Add consistent progress announcements to each long-running command:

**`/zie-implement`**
- Print `[T1/8]` at task start, phase markers inline (→ RED / → GREEN ✓ /
  → REFACTOR ✓), `✓ done — N remaining` at task end
- Checkpoint summary every 3 tasks or at halfway: list completed + remaining
- TaskCreate descriptions verbose enough to read in the UI task list

**`/zie-audit`**
- Print `[Phase 1/5] Project intelligence...` at each phase start
- Per-agent: `  Agent A (Security) ✓` as each completes
- Per-search: `[Research 7/15]` as Phase 3 progresses
- Total at end: "5 phases complete — N findings"

**`/zie-release`**
- Number every gate: `[Gate 1/7] Unit tests...` → `✓` or `✗ FAILED`
- Post-gate steps: `[Step 8/12] Bumping version...` through retro trigger

**`/zie-plan` (multi-slug)**
- Print `[Plan 1/4] drafting...` per slug as agent completes
- Reviewer pass: `  plan-reviewer pass 1...` → `✅` or `❌`

**`/zie-resync`**
- Print "Exploring codebase..." on agent start
- On completion: "✓ Explored N files — drafting knowledge updates"

**`/zie-retro`**
- Print `[ADR 1/3]` as each ADR is written
- Phase markers: "Analyzing git log... ✓", "Updating knowledge docs... ✓"

## Out of Scope

- Time-based ETA (Claude cannot measure wall-clock time reliably)
- Real progress bars or terminal UI control
- Background progress during model inference
