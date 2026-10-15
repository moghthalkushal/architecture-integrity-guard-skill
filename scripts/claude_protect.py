#!/usr/bin/env python3
"""Optional Claude PreToolUse tripwire; not a security boundary.

Inputs JSON on stdin, emits an 'ask' decision for selected edit tools touching
human-owned architecture policy files. Shell writes / other tools can bypass it.
"""
import fnmatch
import json
import os
import sys
from pathlib import Path

PROTECTED = [
    'architecture/canonical-contracts.json',
    'architecture/contracts/**',
    'tests/architecture/**',
    '.dependency-cruiser.*',
    '.github/CODEOWNERS',
    '.github/workflows/architecture-guard.yml',
    '.claude/settings.json',
    '.agents/skills/architecture-integrity-guard/**',
    '.claude/skills/architecture-integrity-guard/**',
]


def get_paths(input_data):
    inp = input_data.get('tool_input', {})
    if not isinstance(inp, dict):
        return []
    names = ('file_path', 'notebook_path', 'path', 'files')
    vals = []
    for k in names:
        val = inp.get(k)
        if isinstance(val, str):
            vals.append(val)
        elif isinstance(val, list):
            vals.extend(x for x in val if isinstance(x, str))
    return vals


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        print('Malformed hook input; no decision', file=sys.stderr)
        return 1
    project = Path(os.environ.get('CLAUDE_PROJECT_DIR', data.get('cwd', os.getcwd()))).resolve()
    for candidate in get_paths(data):
        path = Path(candidate)
        absolute = path.resolve() if path.is_absolute() else (project / path).resolve()
        try:
            rel = absolute.relative_to(project).as_posix()
        except ValueError:
            continue
        if any(fnmatch.fnmatchcase(rel, pattern) or rel == pattern.removesuffix('/**') for pattern in PROTECTED):
            print(json.dumps({'hookSpecificOutput': {
                'hookEventName': 'PreToolUse',
                'permissionDecision': 'ask',
                'permissionDecisionReason': f'Human-owned architectural guardrail: {rel}. Review before editing; branch-protected CI is authoritative.'
            }}))
            return 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
