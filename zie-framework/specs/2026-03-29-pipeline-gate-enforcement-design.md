---
approved: true
approved_at: 2026-03-29
backlog: backlog/pipeline-gate-enforcement.md
---

# Pipeline Gate Enforcement — Design Spec

**Problem:** The SDLC pipeline is advisory — `intent-sdlc.py` injects suggestions but Claude can ignore them, and `/zie-plan` with an explicit slug bypasses the approved-spec check entirely.

**Approach:** Two-layer enforcement. Layer 1: strengthen `intent-sdlc.py` to run pre-condition checks on UserPromptSubmit — when plan/implement intent is detected, verify pipeline state and inject a **directive additionalContext block**. Per CLAUDE.md "Hook Error Handling Convention", hooks always `exit(0)` and never use `blockResponse`. A directive block uses imperative language Claude must follow: `"⛔ STOP. [reason]. Do not proceed."` — this format is treated as a system constraint, not a suggestion. Layer 2: harden `zie-plan.md` pre-flight to hard-stop on missing approved spec regardless of invocation mode. Together these cover both explicit command invocations and ambient "let's code X" prompts.

**Components:**
- `hooks/intent-sdlc.py` — add `_check_pipeline_preconditions(intent, roadmap_content, cwd)` returning a blocking message or None
- `commands/zie-plan.md` — remove explicit-slug bypass; always validate approved spec exists
- `tests/unit/test_hooks_intent_sdlc.py` — new gate-specific test cases

**Data Flow:**

1. User submits prompt
2. `intent-sdlc.py` runs → detect dominant intent via existing PATTERNS
3. Detected intent = `"plan"` →
   - Slug-match: extract all kebab-case tokens and known ROADMAP slugs present in prompt
     (method: load Next-lane slugs from ROADMAP, check if any slug or its human-readable
     form appears in the lowercased prompt — no Thai tokenization needed)
   - If a matched slug has no `approved: true` spec → inject directive block:
     `"⛔ STOP. No approved spec for '<slug>'. You must run /zie-spec <slug> first. Do not proceed with planning."`
   - If no ROADMAP slug matched in prompt → inject soft nudge only (ambiguous prompt — avoid false positives)
4. Detected intent = `"implement"` →
   - Check ROADMAP Now lane for `[ ]` items (incomplete tasks)
   - Per ADR (WIP=1): Now lane should have exactly one `[ ]` feature. Gate check: at least one `[ ]` item present → proceed; zero `[ ]` items → block
   - If no `[ ]` in Now lane: inject directive block: `"⛔ STOP. No active feature in Now lane. Complete /zie-backlog → /zie-spec → /zie-plan first, then start /zie-implement. Do not write code."`
   - If at least one `[ ]` in Now lane: inject normal SDLC context (existing behaviour)
5. `zie-plan.md` pre-flight (all invocation modes, including explicit slug arg) →
   - Glob `zie-framework/specs/*-<slug>-design.md`
   - Read frontmatter; check `approved: true`
   - If file missing → print `"⛔ No spec found for '<slug>'. Run /zie-spec <slug> first."` and stop
   - If `approved: false` → print `"⛔ Spec exists but not approved. Complete /zie-spec <slug> review first."` and stop

6. **Positional guidance** (intent-sdlc.py, any intent) →
   - When prompt contains a known ROADMAP slug and no dominant intent matched yet,
     inject stage-aware nudge based on slug's current pipeline position:
     - In Next, no spec → `"Feature '<slug>' is in backlog. Start with /zie-spec <slug>"`
     - Has approved spec, not in Ready → `"Spec approved for '<slug>'. Run /zie-plan <slug>"`
     - In Ready, not in Now → `"Plan ready for '<slug>'. Run /zie-implement to start"`
   - This runs only when no gate was already triggered (no double-injecting)

**Edge Cases:**

- Feature name in prompt doesn't match any ROADMAP slug → no gate triggered (normal conversation guard)
- Multiple feature names in one prompt → check each; block if any lacks approved spec
- "plan this design pattern" (false positive) → feature-name extractor must require ROADMAP match before triggering gate
- `zie-plan` called with no args → existing behaviour (list approved specs) unchanged
- `zie-plan` called with slug that has approved spec → gate passes, normal flow continues
- `approved: false` in spec frontmatter (draft spec) → gate blocks with: `"⛔ Spec exists but not approved. Complete /zie-spec <slug> review first."`
- Now lane has a `[x]` completed item but no `[ ]` → treated as empty (no active WIP)
- `zie-framework/` directory missing → hook exits 0 silently (outer guard — existing behaviour)

**Out of Scope:**

- `blockResponse` hook output (CLAUDE.md Hook Error Handling Convention: hooks always exit 0; `additionalContext` is the only output mechanism)
- OS-level process blocking (hooks cannot hard-block Claude at syscall level)
- Gate for backlog → spec transition (backlog is optional; spec is the real entry gate)
- Enforcement via PermissionRequest hook (not applicable to conversational flows)
- Retroactive enforcement on already-started work (only gates new intent)
- Blocking `/zie-spec` or `/zie-backlog` (these are always allowed)
- Thai natural-language noun-phrase extraction (slug-matching against known ROADMAP items is sufficient and avoids word-boundary issues)
