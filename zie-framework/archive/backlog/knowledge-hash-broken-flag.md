# lean: fix knowledge-hash --now flag (silent failure)

## Problem

`commands/zie-implement.md:24` invokes
`python3 hooks/knowledge-hash.py --now` but the script's argparse only registers
`--root`. The unrecognized `--now` flag causes `SystemExit(2)`, which is masked
by `2>/dev/null || echo "knowledge-hash: unavailable"`.

Result: the knowledge hash is **never injected** in /zie-implement sessions.

## Motivation

- **Severity**: High
- **Source**: /zie-audit 2026-03-26 finding #7
- Knowledge drift detection in implement sessions is completely non-functional
- Silent failure — no indication to the user that the feature is broken

## Scope

- Either add `--now` flag to knowledge-hash.py argparse, or
- Remove `--now` from the command invocation
- Add integration test verifying the command actually produces output
