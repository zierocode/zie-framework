# Consolidate Reviewer Disk Fallback

## Problem

`spec-reviewer`, `plan-reviewer`, and `impl-reviewer` each carry an identical ~4-step disk-fallback ADR read block. This logic is supposed to live solely in `reviewer-context`, but the three skills duplicated it inline. Any protocol change (e.g., ADR summary awareness) must be applied in four places.

## Motivation

Single source of truth: the fallback belongs in `reviewer-context` only. Removing the inline duplicates from the three reviewer skills reduces ~12 steps of duplicated content, eliminates drift risk, and makes the contract explicit: callers must pass `context_bundle`.

## Rough Scope

- In: remove inline disk-fallback blocks from spec-reviewer, plan-reviewer, impl-reviewer; add contract note "caller must pass context_bundle"
- Out: `reviewer-context` content unchanged; no behavior change when context_bundle is passed correctly
