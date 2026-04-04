# intent-detect recompiles 96 regex patterns on every UserPromptSubmit

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`intent-detect.py` builds `COMPILED_PATTERNS` dict at lines 80-83 on every
invocation. Because hooks are standalone scripts (not long-running processes),
there's no persistent cache — every user message re-compiles all 96 patterns.
This adds unnecessary latency to each prompt and creates a ReDoS surface if any
pattern is complex or the message is adversarially crafted.

## Motivation

Pattern compilation is expensive. A pre-compiled cache file (or simpler patterns)
reduces per-event latency. A max-length guard on the input message prevents ReDoS.
