#!/usr/bin/env python3
"""Consistent error logging for zie-framework hooks.

All hooks should use log_error() to report exceptions to stderr.
This ensures debugging is possible even when hooks swallow errors (ADR-003).
"""
import sys


def log_error(hook: str, op: str, exc: Exception) -> None:
    """Write a structured error message to stderr.

    Args:
        hook: Hook module name (e.g. "stop-handler", "session-resume").
        op: Operation that failed (e.g. "git_status", "read_config").
        exc: The caught exception instance.
    """
    print(f"[zie-framework] {hook}: {op} failed — {exc}", file=sys.stderr)