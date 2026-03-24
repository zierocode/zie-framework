---
approved: true
approved_at: 2026-03-24
backlog: backlog/progress-visibility.md
---

# Progress Visibility for Long-Running Commands — Design Spec

**Problem:** Long-running commands give no feedback about where they are or how much remains. `/zie-audit` can run 3–8 minutes with no intermediate output. `/zie-release` runs 7+ gates sequentially without numbering. The user cannot tell if a command is halfway done or just starting.

**Approach:** Add consistent progress announcements (phase/step counters) to all six long-running commands. Each counter follows the format `[Phase N/M]` or `[TN/M]` or `[Gate N/M]` at each stage start. No behavioral changes — output additions only.

**Components:**
- Modify: `commands/zie-implement.md` — print `[T1/N]` at task start, phase markers (→ RED / → GREEN / → REFACTOR), `✓ done — N remaining` at task end; checkpoint summary every 3 tasks
- Modify: `commands/zie-audit.md` — print `[Phase 1/5]` at each phase; `Agent X (Domain) ✓` per agent; `[Research N/15]` per search
- Modify: `commands/zie-release.md` — print `[Gate N/7]` per gate; `[Step N/12]` for post-gate steps
- Modify: `commands/zie-plan.md` — print `[Plan N/M]` per slug; reviewer pass markers
- Modify: `commands/zie-resync.md` — print "Exploring codebase..." and completion summary
- Modify: `commands/zie-retro.md` — print `[ADR N/M]` per ADR; phase markers for git log and knowledge doc steps

**Acceptance Criteria:**
- [ ] Each command prints a counter at the start of each phase/step
- [ ] Counter format is consistent: `[Phase N/M]`, `[TN/M]`, or `[Gate N/M]`
- [ ] No change to command logic, output content, or behavior beyond added counters
- [ ] User can determine approximate progress mid-run from output alone
- [ ] Counters appear before the work starts (not after)

**Out of Scope:**
- Time-based ETA (Claude cannot measure wall-clock time reliably)
- Real progress bars or terminal UI control
- Background progress during model inference
