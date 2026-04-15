#!/usr/bin/env python3
"""Compute knowledge_hash for a zie-framework project.

Prints the SHA-256 hex digest to stdout.
Usage: python3 hooks/knowledge-hash.py [--root <path>] [--check]
  --check  Compare stored hash in zie-framework/.config to current hash.
           Prints drift warning if mismatch, silent otherwise.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from utils_error import log_error

EXCLUDE = {
    'node_modules', '.git', 'build', 'dist', '.next',
    '__pycache__', 'coverage', 'zie-framework', '.zie'
}
EXCLUDE_PATHS = {'zie-framework/plans/archive', 'zie-framework/archive'}
CONFIG_FILES = [
    'package.json', 'requirements.txt', 'pyproject.toml',
    'Cargo.toml', 'go.mod'
]

parser = argparse.ArgumentParser()
parser.add_argument('--root', default='.')
parser.add_argument('--now', action='store_true',
                    help='Print current hash to stdout (default; accepted for compatibility)')
parser.add_argument('--check', action='store_true',
                    help='Compare stored vs current hash; print drift warning if mismatch')
args = parser.parse_args()

root = Path(args.root)


def compute_hash(root: Path) -> str:
    dirs = sorted(
        str(p.relative_to(root))
        for p in root.rglob('*')
        if p.is_dir()
        and not any(ex in p.parts for ex in EXCLUDE)
        and str(p.relative_to(root)) not in EXCLUDE_PATHS
    )
    counts = sorted(
        f'{d}:{len(list((root / d).iterdir()))}'
        for d in dirs
    )
    configs = ''
    for cf in CONFIG_FILES:
        p = root / cf
        if p.exists():
            configs += p.read_text()
    s = '\n'.join(dirs) + '\n---\n'
    s += '\n'.join(counts) + '\n---\n'
    s += configs
    return hashlib.sha256(s.encode()).hexdigest()


def _compute_max_mtime(root: Path) -> float:
    """Return the maximum mtime of all .md files under root (excluding zie-framework/)."""
    try:
        mtimes = [
            p.stat().st_mtime for p in root.rglob("*.md")
            if "zie-framework" not in p.parts
        ]
        return max(mtimes) if mtimes else 0.0
    except OSError as e:
        log_error("knowledge-hash", "compute_max_mtime", e)
        return 0.0


if args.check:
    try:
        config_path = root / 'zie-framework' / '.config'
        if not config_path.exists():
            sys.exit(0)
        try:
            config = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            sys.exit(0)
        stored = config.get('knowledge_hash', '')
        if not stored:
            sys.exit(0)

        # mtime gate: skip expensive rglob+hash when no .md file has changed
        # Uses CacheManager with mtime invalidation instead of /tmp file
        sys.path.insert(0, str(Path(__file__).parent))
        from utils_cache import get_cache_manager
        cache = get_cache_manager(root)

        # Compute max_mtime to use as mtime source
        max_mtime = _compute_max_mtime(root)

        def _compute_and_hash():
            current = compute_hash(root)
            return current

        # Use config_path as mtime source — if any .md changes, max_mtime changes
        # which means config_path mtime may not catch it. Instead, we use a TTL
        # approach with the hash as value, and invalidate via mtime on config_path.
        # However, the real check is: if the cached hash == stored hash, we're good.
        # We use CacheManager to cache the expensive compute_hash result.
        cached_hash = cache.get("knowledge_mtime", "knowledge-hash-check")
        if cached_hash is not None and cached_hash == stored:
            sys.exit(0)  # cache hit — hash matches stored

        current = compute_hash(root)
        # Cache the computed hash for future checks
        cache.set("knowledge_mtime", "knowledge-hash-check", current, ttl=3600,
                 invalidation="session")
        if current != stored:
            print(
                '[zf] Knowledge drift detected since last session'
                ' — run /resync to update project context'
            )
    except Exception as e:
        log_error("knowledge-hash", "check", e)
        sys.exit(0)
else:
    print(compute_hash(root))
