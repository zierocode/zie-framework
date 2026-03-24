---
approved: true
approved_at: 2026-03-24
backlog: backlog/parallel-model-effort-optimization.md
---

# Parallel Execution + Model/Effort Optimization — Design Spec

**Problem:** Framework skills and commands use suboptimal model selection (haiku for quality-critical code review), no-op `effort` fields on Haiku (effort is only meaningful on Sonnet/Opus), non-official frontmatter fields, and leave significant parallelism opportunities unused — causing unnecessarily slow and expensive execution on large sprint sessions.

**Approach:** Apply a principled taxonomy to every component: (1) assign the right model for the job (haiku for reference/lookup, sonnet for reasoning/quality), (2) use `context: fork` wherever a skill receives a bounded input bundle rather than needing full session history, (3) identify sequential steps that can run in parallel and restructure calling commands, (4) remove dead configuration fields.

**Components:**

Skills modified:
- `skills/impl-reviewer/SKILL.md` — haiku → sonnet, effort: low → medium
- `skills/retro-format/SKILL.md` — add `context: fork`; restructure to receive compact bundle via `$ARGUMENTS`
- `skills/verify/SKILL.md` — add `context: fork`; restructure to receive test results + changed files via `$ARGUMENTS`
- `skills/tdd-loop/SKILL.md` — remove `type: process` (non-official field; effort: low kept for ADR-012 compliance)
- `skills/test-pyramid/SKILL.md` — remove `type: reference` (non-official field; effort: low kept for ADR-012 compliance)
- `skills/spec-reviewer/SKILL.md` — no frontmatter change (effort: low kept; already has `context: fork`)
- `skills/plan-reviewer/SKILL.md` — no frontmatter change (effort: low kept; already has `context: fork`)

Skills created:
- `skills/docs-sync-check/SKILL.md` — new skill: haiku + fork; verifies CLAUDE.md/README match actual commands/skills/hooks on disk

Commands modified:
- `commands/zie-retro.md` — build compact session summary; fork `retro-format` + `docs-sync-check` in parallel; parent writes ADRs while forks run
- `commands/zie-implement.md` — capture test output after GREEN phase; fork `verify scope=tests-only` while doing ROADMAP update + commit prep
- `commands/zie-release.md` — fork combined quality gate (TODOs + secrets + docs sync check) immediately after Gate 1 passes; run parallel with Gate 2 (test-int)
- `commands/zie-spec.md` — effort: high → medium (orchestration only; heavy reasoning delegated to spec-design skill)
- `commands/zie-plan.md` — effort: high → medium (orchestration only; heavy reasoning delegated to write-plan skill)

Test file updated:
- `tests/unit/test_model_effort_frontmatter.py` — update EXPECTED map: impl-reviewer (haiku/low → sonnet/medium), zie-spec/zie-plan (sonnet/high → sonnet/medium), add docs-sync-check (haiku/low); remove impl-reviewer from TestHaikuFiles.EXPECTED_HAIKU list

**Data Flow:**

### impl-reviewer upgrade
Current: `model: haiku, effort: low, context: fork`
Proposed: `model: sonnet, effort: medium, context: fork`
Rationale: Code review is reasoning-heavy. Fork already bounds context to the changed-files bundle. Sonnet cost is justified — this is the primary quality gate preventing regressions from shipping.

### retro-format fork
Current: `model: haiku, effort: low` — runs inline, inherits full session context (up to 1M tokens on Max plan). When session context is large (post-sprint), haiku's 200K limit causes truncation.
Proposed: Add `context: fork`. Caller builds compact JSON summary:
```json
{
  "shipped": ["feat: X", "fix: Y"],
  "commits_since_tag": 23,
  "pain_points": ["session env pollution"],
  "decisions": ["debounce_ms=0 semantics"],
  "roadmap_done_tail": "..."
}
```
Fork receives this bundle via `$ARGUMENTS`. Runs on haiku with bounded input — no context truncation risk regardless of session size.

### verify fork
Current: `model: haiku, effort: low` — runs inline after GREEN phase during `/zie-implement`. Reads test output by re-running tests inside the skill (duplicate work).
Proposed: Add `context: fork`. Caller captures test output from the GREEN phase run, passes as `$ARGUMENTS`:
```json
{
  "test_output": "...",
  "changed_files": ["hooks/auto-test.py", "tests/unit/test_hooks_auto_test.py"],
  "scope": "tests-only"
}
```
Fork checks tests-passed + secrets scan concurrently with caller doing ROADMAP update + commit prep.

**Verify fallback contract (applies to both callers):** If `$ARGUMENTS` is empty or malformed, verify falls back to running `make test-unit` directly (existing behavior). This means `/zie-release` can still call `verify scope=full` without passing captured output — it gets the full inline behavior. The captured-output optimization is opt-in from the caller side; `context: fork` only isolates the context window, it does not change the skill's fallback logic.

### docs-sync-check skill (new)
Input: `$ARGUMENTS` contains git-diff summary (new/changed/deleted command+skill+hook filenames).
Behavior:
1. Read `CLAUDE.md` project structure section.
2. Read `README.md` commands table.
3. Glob actual `commands/*.md`, `skills/*/SKILL.md`, `hooks/*.py`.
4. Compare lists → return JSON: `{claude_md_stale: bool, readme_stale: bool, missing: [], extra: []}`.
Output: structured JSON verdict (caller decides whether to auto-update or surface to user).
Model: haiku, effort: low (enumeration task, no reasoning required; effort: low kept for ADR-012 test compliance). Context: fork (reads fixed set of files, no session history needed).

### zie-retro parallelism
Current sequential: git-log → retro-format (serial) → write ADRs → docs check → ROADMAP update.
Proposed:
1. Parent builds compact summary from git log + ROADMAP.
2. Simultaneously fork: `retro-format` (receives compact summary) + `docs-sync-check` (receives changed-files list from `git diff main..HEAD --name-only`).
3. Parent writes ADRs while forks run.
4. Collect fork results → apply docs updates if stale → ROADMAP update.
Net: retro-format + docs-sync-check run in parallel with ADR writing. Time saved: whichever of the two forks is slower becomes the critical path (was strictly sequential before).

### zie-implement verify overlap
Current: GREEN (run tests) → REFACTOR → verify (re-run tests inside skill, then docs check) → commit.
Proposed:
1. After GREEN: capture test output.
2. Fork `verify scope=tests-only` with captured output as `$ARGUMENTS`.
3. Parent does: REFACTOR (code cleanup only — no test runs needed) + ROADMAP update + git add.
4. Check fork result before `git commit`. If APPROVED → commit. If issues → fix first.
Net: verify and REFACTOR run in parallel. Time saved: verify's test re-run cost eliminated (uses cached output); docs/ROADMAP update overlaps with verify.

### zie-release quality gate parallelism
Current: Gate 1 (unit tests) → Gate 2 (int tests) → Gate 3 (e2e) → Gate 4 (TODOs/secrets) → Gate 5 (docs sync) — all sequential.
Proposed: After Gate 1 passes, immediately fork combined quality agent (TODOs grep + secrets scan + docs-sync-check). Fork runs concurrent with Gate 2 and Gate 3. Collect fork result before version bump step.
Net: TODOs/secrets/docs scan overlaps with up to 2 test suite runs. On large projects where test-int takes 30s+, this is free parallelism.

**Edge Cases:**
- Forked skills receiving empty/malformed `$ARGUMENTS`: each fork must handle gracefully (fall back to disk reads for retro-format; skip docs check and return `{stale: false}` for docs-sync-check).
- `impl-reviewer` cost increase (haiku → sonnet): fork bounds context to changed-files bundle only; typical review is 3-10 files × 200 lines = well within 40K tokens. Cost per review ≈ 2-5x higher but review happens once per task (not per iteration).
- `verify` fork: if caller's captured test output is stale (re-run between capture and fork collect), fork will report on stale data. Mitigation: fork checks mtime of `.pytest_cache/lastfailed` — if newer than output timestamp, note "test re-run detected, output may be stale."
- Parallel forks in `/zie-retro`: if one fork fails (skill error), parent continues and surfaces the failure at collect step — retro is not blocked.
- `effort` field absent from haiku skills: Claude Code already defaults to model's standard reasoning when effort is absent. No behavioral change — removes misleading documentation.

**Out of Scope:**
- Changing haiku → sonnet for spec-reviewer, plan-reviewer (these review structured documents, not code; haiku is adequate and fork already bounds context).
- Parallelizing multiple tasks within `/zie-implement` (WIP=1 constraint is intentional).
- Changing `write-plan` or `spec-design` model/effort (already correctly set to sonnet/high).
- Adding `background: true` agents (current parallel flows use synchronous forks that block at collect point — simpler and sufficient).
- zie-backlog and zie-status commands (haiku is correct; these are lookup/display tasks with no reasoning requirement).
