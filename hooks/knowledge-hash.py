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
import tempfile
import time
from pathlib import Path

EXCLUDE = {
    'node_modules', '.git', 'build', 'dist', '.next',
    '__pycache__', 'coverage', 'zie-framework'
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


def _mtime_cache_path(root: Path) -> Path:
    """Return path to the mtime gate cache file for this project root."""
    import hashlib
    path_hash = hashlib.sha256(str(root.resolve()).encode()).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"zie-kh-{path_hash}.mtime"


def _read_mtime_cache(cache_path: Path) -> float:
    """Return stored mtime float, or 0.0 on any error."""
    try:
        return float(cache_path.read_text().strip())
    except Exception:
        return 0.0


def _write_mtime_cache(cache_path: Path, mtime: float) -> None:
    try:
        cache_path.write_text(str(mtime))
    except Exception:
        pass


def _compute_max_mtime(root: Path) -> float:
    """Return the maximum mtime of all .md files under root (excluding zie-framework/)."""
    try:
        mtimes = [
            p.stat().st_mtime for p in root.rglob("*.md")
            if "zie-framework" not in p.parts
        ]
        return max(mtimes) if mtimes else 0.0
    except Exception:
        return 0.0


if args.check:
    try:
        config_path = root / 'zie-framework' / '.config'
        if not config_path.exists():
            sys.exit(0)
        try:
            config = json.loads(config_path.read_text())
        except Exception:
            sys.exit(0)
        stored = config.get('knowledge_hash', '')
        if not stored:
            sys.exit(0)

        # mtime gate: skip expensive rglob+hash when no .md file has changed
        cache_path = _mtime_cache_path(root)
        written_at = _read_mtime_cache(cache_path)
        max_mtime = _compute_max_mtime(root)
        if written_at > 0.0 and max_mtime <= written_at:
            sys.exit(0)  # cache hit — no files changed since last check

        current = compute_hash(root)
        _write_mtime_cache(cache_path, time.time())
        if current != stored:
            print(
                '[zie-framework] Knowledge drift detected since last session'
                ' \u2014 run /zie-resync to update project context'
            )
    except Exception:
        sys.exit(0)
else:
    print(compute_hash(root))
