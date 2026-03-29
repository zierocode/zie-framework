# ADR-026: ROADMAP Done Section Auto-Compaction

Date: 2026-03-30
Status: Accepted

## Context

ROADMAP.md Done section grows ~2 entries per release. At 36 entries today,
it will reach 150+ entries within 6 months, making the file unwieldy for
manual review. The existing 20-line read limit in `/zie-retro` mitigates
context impact today but could drift if the limit is removed or relaxed.
A self-managing state file aligns with the zie-framework principle that
SDLC artifacts stay readable as the project ages.

## Decision

Add `compact_roadmap_done()` to `hooks/utils.py`. When invoked by the
`retro-format` skill after every ROADMAP Done update: if entry count > 20
and some entries are older than 6 months, compact those old entries into a
single `[archive]` summary line and write their detail to
`zie-framework/archive/ROADMAP-<version-range>.md`. The 20 most-recent
entries always remain in full detail. Threshold and cutoff are hardcoded
(not config) per YAGNI.

## Consequences

**Positive:** Done section stays at ≤ 20 full-detail entries automatically.
Archive files preserve full history. No manual cleanup required.
**Negative:** Old entries are no longer visible in ROADMAP.md directly;
reviewer must follow the archive link.
**Neutral:** Threshold (20) and cutoff (6 months) are hardcoded. Future
parameterization possible via zie-framework/.config (separate backlog item).
