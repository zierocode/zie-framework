# ADR-018: utils.py as Canonical Constants and Helpers Library

Date: 2026-03-25
Status: Accepted

## Context

Hook scripts duplicated constants and logic inline: `BLOCKS`/`WARNS` lists
existed in both `safety-check.py` and `safety_check_agent.py` (requiring an
`importlib` workaround in the latter), `normalize_command()` was re-implemented
as an inline `re.sub` in three hooks, and `SDLC_STAGES` had no single source of
truth. This caused silent divergence and made security-sensitive pattern lists
hard to maintain.

## Decision

`utils.py` is the canonical home for all shared hook constants (`BLOCKS`,
`WARNS`, `SDLC_STAGES`) and normalisation helpers (`normalize_command`). Any
hook that needs these imports from `utils` — no inline copies permitted. New
shared constants must go to `utils.py` first.

## Consequences

**Positive:** Security-sensitive block/warn lists have a single source of truth;
updating them takes effect in all hooks simultaneously. Eliminates importlib
workarounds and 39-line code duplication.
**Negative:** `utils.py` grows over time; contributors must know to look there
before adding a helper to an individual hook.
**Neutral:** Hook files become shorter and more focused on their event logic.
