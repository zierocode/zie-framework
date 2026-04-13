# plan: release-non-claude-fallback

## Steps

### Step 1: Add Non-Claude Advisory to `/release`

**Files:** `commands/release.md`

Insert advisory block (exact text from spec) at line ~55, after the header block, before step 1.

### Step 2: Add `make release-local` Target

**File:** `Makefile`

Add after `implement-local` target (~line 61). Verify `implement-local` exists first as anchor.

### Step 3: Remove Inline Model Comments from `release.md`

**File:** `commands/release.md`

- Line 126: Replace `<!-- model: sonnet reasoning: version suggestion ...-->` with `<!-- NOTE: version suggestion requires judgment about breaking changes -->`
- Line 143: Replace `<!-- model: sonnet reasoning: narrative rewrite ...-->` with `<!-- NOTE: narrative rewrite produces human-readable commit history -->`

### Step 4: Remove Inline Model Comment from `impl-reviewer/SKILL.md`

**File:** `skills/impl-reviewer/SKILL.md`

- Line 46: Replace `<!-- model: sonnet escalation note: ... escalate to sonnet reasoning. -->` with `<!-- NOTE: escalate to a reasoning-capable model if available -->`

### Step 5: Run Tests

**Command:** `make test-unit`

## Verification

- [ ] `commands/release.md` contains non-Claude advisory in pre-flight section
- [ ] `Makefile` contains `release-local` target
- [ ] `commands/release.md` has no `<!-- model: sonnet reasoning -->` comments
- [ ] `skills/impl-reviewer/SKILL.md` has no `<!-- model: sonnet escalation note -->` comment
- [ ] `hooks/subagent-context.py` env var handling — verified already correct (no action needed)
- [ ] `make test-unit` passes
