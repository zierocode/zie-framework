---
tags: [chore]
---

# Pre-flight Consolidation

## Problem

10 commands each independently repeat the same 3–5 guard steps verbatim (~150 words each):
check `zie-framework/` exists → read `.config` → check ROADMAP Now lane for WIP conflict.
This is ~1,500 words of pure copy-paste with no variation.

## Motivation

Creating a canonical `command-conventions.md` and replacing each pre-flight section with a
single reference line saves ~1,200 words (~7% of total corpus) and creates a single source
of truth. Any future change to the guard protocol touches one file instead of ten.

## Rough Scope

- Create `zie-framework/project/command-conventions.md` with the standard pre-flight protocol
- Replace the `## ตรวจสอบก่อนเริ่ม` section in all 10 commands with a 1-line reference
- Commands with custom pre-flight logic (e.g. init.md) keep their variant inline
- Update any tests that assert specific guard text to use the reference doc format
