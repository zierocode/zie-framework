# session-learn.py pending file write has no locking

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

`session-learn.py:29-40` writes to `pending_learn_file` in
`~/.claude/projects/{project}/` without any file lock. If two Claude sessions
close simultaneously (e.g., two terminal tabs), both may write concurrently and
corrupt the file. The next session reads a malformed JSON blob.

## Motivation

Atomic writes (write to `.tmp` then `rename`) are the standard pattern for safe
single-file state. Cost is negligible; benefit is correctness under concurrent use.
