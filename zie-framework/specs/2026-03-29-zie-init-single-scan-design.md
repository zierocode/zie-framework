---
approved: true
approved_at: 2026-03-29
backlog: backlog/zie-init-single-scan.md
---

# zie-init Single-Pass Scan — Design Spec

**Problem:** `/zie-init` executes two separate filesystem scans on existing projects — the Explore agent scan (step 2a) and a separate directory rescan for migratable documentation (step 2h) — creating redundant I/O and latency for large codebases.

**Approach:** Extend the Explore agent prompt to include migration detection in its output, parsing the result into a `migratable_docs` object. Remove the separate step 2h filesystem scan entirely. This consolidates pattern detection into a single agent invocation while maintaining detection accuracy through prompt engineering.

**Components:**
- `commands/zie-init.md` — update Explore agent prompt to include migration detection; remove step 2h directory rescan; parse `migratable_docs` from agent JSON and present migration candidates

**Data Flow:**
1. User runs `/zie-init` on existing project
2. Detect greenfield vs existing (unchanged)
3. If existing: invoke Explore agent with expanded prompt (step 2a):
   - Prompt now includes: "Also list all files matching `**/specs/*.md`, `**/spec/*.md`, `**/plans/*.md`, `**/plan/*.md`, `**/decisions/*.md`, `**/adr/*.md`, `ADR-*.md` at project root — return as `migratable_docs` object with `specs`, `plans`, `decisions` keys"
   - Agent returns structured JSON report (same structure as before, with added `migratable_docs` key at top level)
4. Agent report is parsed by zie-init command:
   - Extract `agent_report.migratable_docs` (expected structure: `{"specs": ["path/to/spec.md"], "plans": [], "decisions": ["path/to/adr.md"]}`)
   - If `migratable_docs` missing or empty → skip migration step silently
5. Present migration candidates to user (unchanged, uses parsed list instead of rescanned files)
6. Execute user choice (yes/no/select) using `git mv` (unchanged)
7. Continue to step 3 (create zie-framework/ structure)
8. REMOVED: old step 2h directory rescan — no longer needed

**Edge Cases:**
- Agent returns empty `migratable_docs` object or missing key → skip migration step silently (functional parity with current behavior)
- Agent returns malformed JSON or fails to include `migratable_docs` → use empty object `{}` as fallback; warn "Could not detect migratable docs from agent report"
- Agent times out → fall back to skipping migration step (no error) with warning "Agent scan incomplete, skipping migration detection"
- `**/backlog/*.md` files exist → agent prompt explicitly includes this pattern in detection request (backlog/* explicitly listed)
- Files already in `zie-framework/` → agent should exclude these in glob patterns (same as current step 2h exclusion rules)
- Symlinks or relative paths in spec/plan/decisions directories → agent returns paths as-is; zie-init validates existence before presenting to user
- User provides invalid JSON or garbled agent response → graceful degradation: skip migration, continue with step 3
- Migration candidate exists in both source and destination → `git mv` will fail; present this error to user with retry option

**Out of Scope:**
- Changes to zie-init template logic or project-type detection
- Changes to knowledge_hash computation or knowledge file generation
- Changes to migration file destinations or skip rules (README, CHANGELOG, LICENSE, CLAUDE.md, etc.)
- Playwright/zie_memory branch logic
- Makefile or VERSION creation
- ROADMAP or .config generation
