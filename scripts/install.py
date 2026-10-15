#!/usr/bin/env python3
"""Copy this portable skill to Codex and/or Claude Code project skill dirs."""
import argparse
import shutil
import sys
from pathlib import Path

NAME = 'architecture-integrity-guard'
TARGETS = {
    'codex': '.agents/skills',
    'claude': '.claude/skills',
}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True, help='project root')
    p.add_argument('--targets', choices=['both', 'codex', 'claude'], default='both')
    p.add_argument('--init-starters', action='store_true', help='copy examples with .example suffix only; never overwrite')
    p.add_argument('--overwrite', action='store_true', help='replace existing skill copies; review changes first')
    args = p.parse_args()
    source = Path(__file__).resolve().parent.parent
    root = Path(args.repo).resolve()
    if not root.is_dir():
        p.error('--repo must point to an existing directory')
    targets = TARGETS.items() if args.targets == 'both' else [(args.targets, TARGETS[args.targets])]
    for name, relative in targets:
        target = root / relative / NAME
        if target.exists() and not args.overwrite:
            print(f'SKIP existing {target} (use --overwrite to replace after review)')
            continue
        if target.resolve() == source.resolve():
            print(f'SKIP source == target: {target}')
            continue
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'tests'))
        print(f'INSTALLED {name}: {target}')
    if args.init_starters:
        destdir = root / 'architecture'
        destdir.mkdir(exist_ok=True)
        dest = destdir / 'canonical-contracts.example.json'
        if not dest.exists():
            shutil.copy2(source / 'templates' / 'canonical-contracts.example.json', dest)
            print(f'COPIED example: {dest}; customize then rename to canonical-contracts.json')
        else:
            print(f'SKIP existing {dest}')
    print('NEXT: adapt the architecture manifest; configure repo-specific CI and CODEOWNERS; add the invocation snippets to project instructions.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
