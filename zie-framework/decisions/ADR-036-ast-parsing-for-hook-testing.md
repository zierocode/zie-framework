# ADR-036 — AST Parsing for Testing Hooks with Module-Level Side Effects

**Status:** Accepted
**Date:** 2026-04-01

## Context
hooks/intent-sdlc.py executes sys.exit(0) at module level when event parsing fails. This prevents the module from being imported in tests. importlib.machinery.SourceFileLoader also fails because module execution triggers sys.exit().

## Decision
Use Python's ast module to parse the hook source code as text and extract dict literals (PATTERNS, SUGGESTIONS) without executing the module. _extract_dict_literal(source, var_name) uses ast.parse + ast.iter_child_nodes to find module-level dict assignments.

## Consequences
**Positive:** Tests run without subprocess overhead. Pattern changes are immediately testable. Pattern: re-usable for any hook that cannot be imported.
**Negative:** AST extraction is more complex than direct import. Only extracts simple dict literals (not computed values).
**Neutral:** Already used in test_intent_sdlc_regex.py — this extends an established pattern.

## Alternatives
- subprocess test: spawns python process per test — slow and brittle
- Mock sys.exit: complex patching required at import time
- Refactor hook to importable module: changes production code to serve tests
