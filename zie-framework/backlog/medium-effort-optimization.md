---
id: medium-effort-optimization
title: Sonnet 4.6 medium-effort adaptation
priority: medium
created: 2026-03-27
source: deep-analysis-2026-03-27
---

## Problem

Framework was designed with `effort: high` in skill frontmatter and assumes high/max model effort
throughout. Zie has switched to Sonnet 4.6 medium effort globally. Mismatches cause:
- Skills declaring `effort: high` don't match the actual runtime setting
- Long-running skills (spec-design, zie-audit) may lose context across compaction at medium effort
- Deferred impl-reviewer polling burns tokens unnecessarily when waiting

## Motivation

Maintain full functionality under Sonnet 4.6 medium effort without degrading SDLC quality.

## Acceptance Criteria

- [ ] All skill frontmatter updated: `effort: medium` (or `effort: high` where genuinely required with justification)
- [ ] Command frontmatter effort fields audited and corrected
- [ ] Lazy-load ROADMAP: hooks and skills load Now-lane only (10–20 items) instead of full file
- [ ] Long-running skills (spec-design, zie-audit) have explicit phase checkpoints documented
- [ ] Deferred impl-reviewer polling frequency reduced (e.g., poll once at stop, not continuously)
- [ ] ADR documenting effort-level strategy for framework components

## Scope

- `skills/*/SKILL.md` — update effort fields
- `commands/*.md` — update effort fields
- `hooks/utils.py` — lazy-load ROADMAP (parse Now section only by default)
- `zie-framework/decisions/` — new ADR: effort routing strategy
