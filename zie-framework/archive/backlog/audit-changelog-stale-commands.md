# CHANGELOG references removed commands /zie-ship and /zie-build

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`CHANGELOG.md:162-169` (v1.1.0 section) mentions `/zie-ship` and `/zie-build`
which no longer exist. While CHANGELOG is historical, users reading old releases
may attempt these commands and get confused by a "command not found" result.

## Motivation

Add a `[REMOVED]` annotation or a note in the v1.1.0 section pointing to the
replacement commands (`/zie-implement`, `/zie-release`). Low effort, prevents
user confusion.
