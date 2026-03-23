# No signed releases or SLSA provenance

**Severity**: Low | **Source**: audit-2026-03-24 (SLSA framework)

## Problem

Release tags are unsigned and there's no SLSA provenance file documenting how
the package was built. SLSA Level 1 minimum requires provenance showing build
platform, build process, and source commit. OpenSSF Scorecard's `Signed-Releases`
check fails.

## Motivation

For a tool installed into developer workflows, supply chain trust matters. SLSA
L1 is a one-time documentation effort; signed tags require `gpg` or GitHub's
attestation action. Low effort, high trust signal.
