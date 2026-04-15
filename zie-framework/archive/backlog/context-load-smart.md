---
tags: [feature]
---

# context-load-smart — Deduplicate Context Loading

## Problem

Context loading is duplicated across commands and skills. Each reviewer re-reads ADRs and ROADMAP independently, burning tokens and adding latency.

## Motivation

Single load-context entry point with session caching eliminates redundant disk reads and keeps context bundles lean.

## Rough Scope

- Universal load-context skill as single entry point
- Session cache with content hash (invalidate on file change)
- Reviewer context_bundle passthrough (no re-read)
- ROADMAP session cache (mtime-gated)

<!-- priority: HIGH -->
<!-- depends_on: context-loader-sprint -->
