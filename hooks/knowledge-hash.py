#!/usr/bin/env python3
"""Compute knowledge_hash for a zie-framework project.

Prints the SHA-256 hex digest to stdout.
Usage: python3 hooks/knowledge-hash.py [--root <path>]
"""
import argparse
import hashlib
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
                    help='Print current hash to stdout (default behavior; accepted for compatibility)')
args = parser.parse_args()

root = Path(args.root)
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
print(hashlib.sha256(s.encode()).hexdigest())
