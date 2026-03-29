---
approved: true
approved_at: 2026-03-29
backlog: backlog/user-onboarding-sdlc.md
---

# User Onboarding + Knowledge Drift Detection — Design Spec

**Problem:** New users get no pipeline orientation after `/zie-init`, and returning users don't see when project structure has drifted from cached knowledge. Two small UX gaps that break the self-documenting workflow.

**Approach:** Add two minimal outputs to existing hooks. In `/zie-init` (step 13, post-summary), print a 3-line SDLC pipeline diagram so users understand the flow. In `session-resume.py`, invoke `knowledge-hash.py --check` to detect drift and warn if the hash has changed since last session. Both are 5-15 line additions to existing code; both exit cleanly if optional utilities are missing.

**Components:**
- `commands/zie-init.md` — add pipeline summary to Step 13 (post-init output)
- `hooks/session-resume.py` — add drift detection after active feature print
- `hooks/knowledge-hash.py` — add `--check` mode to compare stored vs current hash
- `zie-framework/.config` — leverage existing `knowledge_hash` field (no schema change)
- `tests/unit/test_hooks_session_resume.py` — test drift detection and silent pass-through
- `tests/unit/test_commands_zie_init.py` — verify pipeline summary in output

**Data Flow:**

1. **User runs `/zie-init` in new project**
2. Steps 1-12 execute normally (detection, knowledge scan, file creation)
3. Step 13 prints summary; immediately after, print:
   ```
   SDLC pipeline:
     /zie-backlog → /zie-spec → /zie-plan → /zie-implement → /zie-release → /zie-retro
   Each stage enforces quality gates. Run /zie-status to see where you are.
   First feature: /zie-backlog "your idea"
   ```
4. If migration was run in step 2.h, append:
   ```
   Migration complete: <N> files moved to zie-framework/specs|plans|decisions/
   ```
5. **User returns to project in next session**
6. `SessionStart` hook fires → `session-resume.py` executes
7. Print active feature (existing behavior)
8. Call `knowledge-hash.py --check` (new mode) with no arguments
9. `--check` mode:
   - Read stored `knowledge_hash` from `zie-framework/.config`
   - Compute current hash (existing hash logic)
   - If stored hash missing/empty → silently exit (fresh init or greenfield)
   - If hashes match → silently exit
   - If mismatch → print drift warning to stdout:
     ```
     [zie-framework] Knowledge drift detected since last session — run /zie-resync to update project context
     ```
10. Session continues normally

**Edge Cases:**

- Fresh `/zie-init` (greenfield): `knowledge_hash` is empty string → `--check` silently skips drift detection
- Existing project just initialized: knowledge_hash is populated in step 2.f → first return session detects any drift since init
- `knowledge-hash.py` crashes or times out: outer guard in `session-resume.py` catches exception, prints to stderr, exits 0 (never blocks Claude)
- `zie-framework/` missing entirely: `session-resume.py` already has `if not zf.exists(): sys.exit(0)` guard at top
- `.config` file missing: `load_config()` returns `{}` per ADR-019, so `config.get("knowledge_hash", "")` returns empty string → skip drift check
- Multi-session rapid changes (frequent git operations): hash recompute is deterministic, no race condition possible
- User modifies `knowledge_hash` manually in `.config`: next session will compute fresh hash and detect mismatch (expected behavior)

**Out of Scope:**

- Automatic re-run of `/zie-resync` (user must explicitly request)
- Partial/selective resync (always full re-scan)
- Diff output (only boolean: drift yes/no)
- Multi-workspace support (one `.config` per project root)
- Knowledge drift in zie-memory (separate persistence layer; not relevant to local hash)
- Performance optimization of `knowledge-hash.py` itself (existing script is adequate)
- Migration success confirmation in `/zie-init` output (migrations already print per item)
- Hash rollback or version history (stateless design: current vs stored only)
