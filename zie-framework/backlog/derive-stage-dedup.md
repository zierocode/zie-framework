---
tags: [chore]
---

# Extract derive_stage() to Shared Utility

## Problem

SDLC stage detection logic (`derive_stage()`) is implemented 3 times with nearly identical keyword-to-stage mapping:
- `intent-sdlc.py` line 249
- `session-stop.py` line 191
- `session-learn.py` line 27

~60 lines of duplicated logic across 3 files.

## Motivation

Code duplication means bug fixes or stage additions must be applied in 3 places. A shared utility eliminates this maintenance risk.

## Rough Scope

**In:**
- Move `derive_stage()` to `utils_roadmap.py` (it already contains roadmap utilities)
- Update all 3 callers to import from `utils_roadmap`
- Add unit test for the shared function

**Out:**
- Changing stage detection logic
- Changing stage keywords