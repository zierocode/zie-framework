---
approved: true
approved_at: 2026-03-24
backlog: backlog/docs-sync-and-completeness.md
---

# Docs: Sync and Completeness Pass — Design Spec

**Problem:** PROJECT.md shows Version 1.6.0 (actual: 1.8.0), `make bump` does not call `sync-version` so PROJECT.md drifts on every release. architecture.md version history stops at v1.4.0. PROJECT.md has Thai table headers ("ทำอะไร"). `knowledge-hash.py` exists on disk but is undocumented in components.md.

**Approach:** Six targeted doc edits — no code changes. (1) Run `make sync-version` to fix current version drift; (2) Add `sync-version` as a recipe step in `bump` to prevent future drift; (3) Fill architecture.md version history for v1.5.0–v1.8.0; (4) Standardize PROJECT.md table headers to English; (5) Add optional deps note to CLAUDE.md Tech Stack + cross-reference to agent mode section; (6) Document `knowledge-hash.py` in components.md as a utility script. README Skills section and project structure diagram are low-priority cosmetic items handled in the same pass.

**Components:**

- `Makefile` — add `sync-version` as a step in the `bump` target (after VERSION + plugin.json are updated, also update PROJECT.md)
- `zie-framework/PROJECT.md` — fix Version 1.6.0 → 1.8.0; change "ทำอะไร" → "Description" in Commands table
- `zie-framework/project/architecture.md` — extend Version History with v1.5.0–v1.8.0 summaries
- `zie-framework/project/components.md` — add `knowledge-hash.py` entry (utility script, not a hook)
- `CLAUDE.md` — add optional deps note to Tech Stack; add `make sync-version` to Development Commands
- `README.md` — add Skills section (brief, mirrors PROJECT.md); fix project structure tree if it shows extra `project/` nesting

**Data Flow:**

**1. Makefile bump target — add sync-version:**

BEFORE:
```makefile
bump: ## Atomically bump VERSION + plugin.json (usage: make bump NEW=1.2.3)
    ...
    @printf '%s\n' "$(NEW)" > VERSION
    @sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
    @echo "Bumped to v$(NEW)"
```

AFTER:
```makefile
bump: ## Atomically bump VERSION + plugin.json + PROJECT.md (usage: make bump NEW=1.2.3)
    ...
    @printf '%s\n' "$(NEW)" > VERSION
    @sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
    @$(MAKE) sync-version
    @echo "Bumped to v$(NEW)"
```

**2. PROJECT.md — version + table header:**

Line 7: `**Version**: 1.6.0  **Status**: active` → `**Version**: 1.8.0  **Status**: active`
Line 13: `| Command | ทำอะไร |` → `| Command | Description |`

**3. architecture.md — Version History entries:**

Add after the v1.4.0 entry:
```
- **v1.5.0** (2026-03-23) — `parse_roadmap_section()` dedup; `knowledge-hash.py`
  extracted as standalone utility; `read_event()`/`get_cwd()` boilerplate dedup
  in utils; CHANGELOG annotations + SECURITY.md + Dependabot config.
- **v1.6.0** (2026-03-23) — Session-wide agent modes (`zie-implement-mode`,
  `zie-audit-mode`); `notification-log` hook for permission/idle events;
  model+effort pinned on all skills and commands.
- **v1.7.0** (2026-03-23) — 23-item sprint implementing v1.6.0 audit findings;
  Bandit B108 suppressions via config; pre-existing test pollution fixes.
- **v1.8.0** (2026-03-24) — Parallel model-effort optimization — faster skill
  execution via parallel model selection; model:haiku for fast-path reviewers.
```

**4. components.md — knowledge-hash.py:**

Add an entry in the hooks section (or utility scripts subsection):
```
### Utility Scripts (not hook event handlers)

| Script | Purpose |
| --- | --- |
| `hooks/knowledge-hash.py` | Compute SHA-256 of project structure for drift detection. Called by `make resync` / `/zie-resync`. Not registered in hooks.json. |
```

**5. CLAUDE.md — optional deps + sync-version:**

Add after the Tech Stack bullet list:
```markdown
### Optional Dependencies

| Dependency | Purpose | Required? |
| --- | --- | --- |
| `pytest` + `pytest-cov` | Unit + integration test runner | For `make test` |
| `coverage` | Subprocess coverage measurement | For `make test-unit` |
| `playwright` | Browser automation for frontend hooks | Only if `playwright_enabled: true` |
| zie-memory API | Cross-session memory persistence | Only if `zie_memory_enabled: true` |
```

Add to Development Commands section:
```bash
make sync-version  # sync plugin.json + PROJECT.md version to match VERSION file
```

**6. README.md — Skills section:**

Add a "Skills" section after Commands (or before Configuration), matching PROJECT.md:
```markdown
## Skills

Skills are invoked automatically by commands as subagents — not called directly.

| Skill | Purpose |
| --- | --- |
| `spec-design` | Draft design spec from backlog item |
| `spec-reviewer` | Review spec for completeness and correctness |
| `write-plan` | Convert approved spec into implementation plan |
| `plan-reviewer` | Review plan for feasibility and test coverage |
| `tdd-loop` | RED/GREEN/REFACTOR loop for a single task |
| `impl-reviewer` | Review implementation against spec and plan |
| `verify` | Post-implementation verification gate |
| `test-pyramid` | Test strategy advisor |
| `retro-format` | Format retrospective findings as ADRs |
| `debug` | Systematic bug diagnosis and fix path |
| `zie-audit` | 9-dimension audit analysis (invoked by /zie-audit) |
```

**Edge Cases:**
- `make sync-version` regex: `sed -i '' 's/\*\*Version\*\*: [0-9.]*/\*\*Version\*\*: '"$(cat VERSION)"'/'` — already handles the exact PROJECT.md format. Adding it to `bump` is safe since `sync-version` is idempotent.
- `make release` target does NOT call `bump` — it does its own `sed` on plugin.json and does not update PROJECT.md. Not fixing `release` in this item (it calls `--amend` which is a different problem). Add a note in CLAUDE.md Development Commands that `make sync-version` should also be called before `make release`.
- architecture.md version dates: all listed as 2026-03-23 or 2026-03-24 (correct per git log).
- README.md project structure: CLAUDE.md shows the correct structure without extra `project/` nesting. Verify README before editing — only change if the nesting is actually wrong in the current file.
- `knowledge-hash.py` is in `hooks/` but is not a hook event handler. It's a utility CLI script invoked by the `/zie-resync` command skill. The components.md entry should clarify this distinction to avoid confusion.

**Out of Scope:**
- Fixing `make release` to call `sync-version` — release uses `--amend` which is a separate pattern; changes to release process are out of scope
- CHANGELOG.md overlap in v1.7.0/v1.8.0 descriptions — cosmetic, not a correctness issue
- README.md Troubleshooting section generics — not a sync issue, content quality improvement
- Adding `zie_memory_enabled` explanation to CLAUDE.md body — it's adequately explained by the optional deps table
