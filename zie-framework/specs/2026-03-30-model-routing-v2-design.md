# Model Routing v2 — Design Spec

**Problem:** /zie-release and impl-reviewer use sonnet for all steps, but 80-90% of their operations are mechanical tasks (I/O, git commands, checklist checks) that haiku handles equally well, making them 5-8x more expensive than necessary.

**Approach:** Downgrade the default model to haiku for both commands/skills, then identify and annotate the specific steps that genuinely require sonnet reasoning (version bump rationale for release; architectural/security analysis for impl-reviewer). This reduces cost 30-40% with no quality degradation.

**Components:**
- `commands/zie-release.md` (frontmatter + inline model overrides)
- `skills/impl-reviewer/SKILL.md` (frontmatter + guidance comment)
- Test file: `tests/test_model_effort_frontmatter.py` (update EXPECTED map)

**Data Flow:**

1. **zie-release.md:**
   - Change frontmatter `model: sonnet` → `model: haiku`
   - Identify 2 sonnet-only steps:
     - Version suggestion (compare commits to semver rules) → `<!-- model: sonnet -->`
     - CHANGELOG narrative draft → `<!-- model: sonnet -->`
   - All other steps (pre-flight checks, gate collection, file writes, git operations, make invocation) remain haiku

2. **impl-reviewer/SKILL.md:**
   - Change frontmatter `model: sonnet` → `model: haiku`
   - Add guidance comment in Phase 2 (Review Checklist):
     ```
     <!-- model: sonnet escalation note: If this review detects new patterns,
     security concerns, or architectural changes, flag for human review or
     escalate to sonnet reasoning. -->
     ```
   - Routine checks (AC coverage, test exists, no secrets) run on haiku
   - Complex cases (architecture, security, new patterns) get flagged for manual escalation

3. **Test update:**
   - Update `EXPECTED` map in `test_model_effort_frontmatter.py`:
     - `zie-release` → `haiku`
     - `impl-reviewer` → `haiku`

**Edge Cases:**
- Release without version bump (edge case, but all other steps still haiku-safe)
- Impl-reviewer flagging complex case when human reviewer unavailable (documented as "flag for escalation")
- Sonnet model override inline syntax not recognized by Claude Code (fallback: treat as haiku, user can manually re-run with sonnet if needed)

**Out of Scope:**
- Dynamic model selection at runtime
- Changing model for `spec-design`, `write-plan`, `zie-retro`, `zie-audit`, `zie-implement` — these genuinely require sonnet reasoning
- Adding new haiku/sonnet boundaries within steps (only step-level granularity)
