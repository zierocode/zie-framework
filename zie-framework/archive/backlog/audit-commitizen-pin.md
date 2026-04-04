# Pin commitizen Python package version

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`commitizen` (the Python `cz` package used for conventional commits) has no
pinned version in any manifest file — no `requirements.txt` exists (see
`audit-pytest-cve-requirements`). Historical transitive dep issues in the
ecosystem mean an unpinned install could silently pick up a breaking version.

## Motivation

Once `requirements-dev.txt` is created (audit-pytest-cve-requirements), add
a pinned commitizen version entry. Low effort — just add one line to the
manifest once it exists.
