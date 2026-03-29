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
from pathlib import Path

EXCLUDE = {
    'node_modules', '.git', 'build', 'dist', '.next',
    '__pycache__', 'coverage', 'zie-framework'
}
EXCLUDE_PATHS = {'zie-framework/plans/archive'}
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
        current = compute_hash(root)
        if current != stored:
            print(
                '[zie-framework] Knowledge drift detected since last session'
                ' \u2014 run /zie-resync to update project context'
            )
    except Exception:
        sys.exit(0)
else:
    print(compute_hash(root))
