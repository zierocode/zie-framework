# No test for very long commands in safety-check (ReDoS surface)

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`safety-check.py` applies regex patterns to arbitrary bash commands with no
length limit. The test suite has no test for commands >10,000 characters or
adversarially crafted inputs designed to cause catastrophic backtracking on any
of the 22 patterns.

## Motivation

Add a test asserting that safety-check completes within a timeout for very long
inputs (e.g., `"a" * 100000`). Documents the performance contract and catches any
future ReDoS regressions.
