# Makefile release target doesn't verify main branch is clean

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`Makefile:35-39` does `git checkout main` then merges/tags without first verifying
the working tree is clean or that the correct branch is checked out. Running
`make release` accidentally from a dirty dev branch could produce a corrupted
release tag.

## Motivation

Add a `git diff --quiet && git diff --cached --quiet` pre-check or a `git status
--porcelain` assertion before the release steps. Prevents accidental dirty releases.
