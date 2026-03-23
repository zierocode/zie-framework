# Knowledge hash algorithm duplicated in 3 command files

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

The Python inline code for computing `knowledge_hash` appears identically in
`zie-init.md`, `zie-status.md`, and `zie-resync.md`. If the hash algorithm or
file list changes, all three must be updated in sync.

## Motivation

Extract the hash logic into a standalone script (`hooks/knowledge-hash.py`) that
all three commands invoke via Bash. Single source of truth for knowledge drift
detection.
