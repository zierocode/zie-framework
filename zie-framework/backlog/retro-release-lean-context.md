# Retro + Release Context Lean — Fix ROADMAP Double-Read and Parallel Fallback

## Problem

Two specific context efficiency issues in the heaviest commands:

**1. `/zie-retro` reads ROADMAP.md twice:**
The main flow reads Now + Done sections (targeted, ~40 lines). Then two parallel
background Agents are spawned to write back to ROADMAP.md — but each agent re-reads
the full ROADMAP file before writing, creating a race condition risk and redundant
full-file load.

**2. `/zie-release` parallel gate has a blocking fallback:**
`docs-sync-check` Agent runs with `run_in_background=true` in parallel with the
Bash TODOs/secrets scan. But the fallback comment says: "if Agent tool unavailable,
call Skill(zie-framework:docs-sync-check) inline" — which blocks the entire release
flow while sync check runs sequentially.

## Motivation

`/zie-retro` and `/zie-release` are the two commands that run after every sprint —
they should be as fast and efficient as possible. The ROADMAP double-read adds
unnecessary latency (and a potential write conflict if both agents read stale content).
The blocking release fallback defeats the parallel gate design.

## Rough Scope

**zie-retro.md — pre-extract ROADMAP sections:**
- In the main flow, after reading Now + Done sections, extract the relevant
  content into the compact JSON bundle (already done for `roadmap_done_tail`)
- Pass the pre-extracted content to both parallel background agents:
  `"done_section_current": "<extracted text>"`
- Agents write the updated section directly without re-reading the full file
- Use file offset writes (seek to Done section position) rather than full-file
  rewrite to avoid conflicts

**zie-release.md — remove blocking fallback:**
- Replace "fallback: call Skill inline" with:
  "fallback: print '[zie-framework] docs-sync-check unavailable — skipping (manual
  check: make docs-sync)'" and continue
- Release should never block waiting for a non-critical sync check
- Add `make docs-sync` as a standalone manual target so users can run it separately

**Tests:**
- retro parallel agents receive pre-extracted content, don't re-read ROADMAP
- release continues without blocking when Agent tool unavailable
- release prints clear skip message when fallback triggers
