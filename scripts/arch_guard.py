#!/usr/bin/env python3
"""Portable, dependency-free, deliberately scoped architecture contract checker.

Checks: config validity, canonical file existence, discovered/registered consumer
file parity, and static Python AST forbidden imports. Does NOT prove runtime paths,
semantic equality, TS/JS imports or framework route enumeration.
"""
import argparse
import ast
import importlib.util
import json
import sys
from pathlib import Path, PurePosixPath


def clean_rel(value, what, *, glob_ok=False):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{what}: expected nonempty relative path')
    p = value.replace('\\', '/')
    if p.startswith('/') or (len(p) > 1 and p[1] == ':') or '..' in PurePosixPath(p).parts:
        raise ValueError(f'{what}: absolute and parent-traversal paths are not allowed: {value!r}')
    if not glob_ok and any(c in p for c in '*?[]'):
        raise ValueError(f'{what}: glob characters not allowed: {value!r}')
    return p.lstrip('./')


def get_config(root, config):
    config_path = Path(config)
    if not config_path.is_absolute():
        config_path = root / config_path
    if not config_path.is_file():
        raise ValueError(f'CONFIG MISSING: {config_path} — NOT VERIFIED; customize the example manifest first')
    try:
        obj = json.loads(config_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'Invalid JSON manifest: {exc}') from exc
    if not isinstance(obj, dict) or obj.get('version') != 1:
        raise ValueError('Expected a JSON object with "version": 1')
    caps = obj.get('capabilities')
    if not isinstance(caps, list) or not caps:
        raise ValueError('Manifest needs at least one nonempty capability; cannot claim pass with zero checks')
    return obj


def validate(root, config):
    errors = []
    capabilities = config['capabilities']
    seen = set()
    normalized_caps = []
    for idx, cap in enumerate(capabilities):
        label = f'capabilities[{idx}]'
        if not isinstance(cap, dict):
            errors.append(f'{label}: must be an object')
            continue
        ident = cap.get('id')
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            errors.append(f'{label}: id must be unique nonempty text')
        seen.add(ident)
        try:
            canonical = clean_rel(cap.get('canonical'), label + '.canonical')
            globs = cap.get('consumer_globs')
            consumers = cap.get('consumers')
            if not isinstance(globs, list) or not globs:
                raise ValueError(f'{label}.consumer_globs: provide at least one discovery glob')
            if not isinstance(consumers, list) or not consumers:
                raise ValueError(f'{label}.consumers: provide at least one checked-in consumer file')
            globs = [clean_rel(g, label + '.consumer_globs[]', glob_ok=True) for g in globs]
            consumers = [clean_rel(p, label + '.consumers[]') for p in consumers]
            if len(consumers) != len(set(consumers)):
                errors.append(f'{label}: consumers has duplicate paths')
            for p in [canonical] + consumers:
                if not (root / p).is_file():
                    errors.append(f'{label}: missing file {p}')
            discovered = set()
            for pattern in globs:
                discovered.update(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())
            if not discovered:
                errors.append(f'{label}: consumer globs matched no files (do not treat empty inventory as success)')
            for missing in sorted(discovered - set(consumers)):
                errors.append(f'{label}: UNREGISTERED CONSUMER {missing}')
            for stale in sorted(set(consumers) - discovered):
                errors.append(f'{label}: REGISTERED CONSUMER NOT DISCOVERED {stale}')
            raw_rules = cap.get('python_forbidden_imports', [])
            if not isinstance(raw_rules, list):
                raise ValueError(f'{label}.python_forbidden_imports: expected list')
            rules = []
            for rno, rule in enumerate(raw_rules):
                if not isinstance(rule, dict):
                    raise ValueError(f'{label}.python_forbidden_imports[{rno}]: expected object')
                modules = rule.get('modules', [])
                allows = rule.get('allow_files', [])
                if not isinstance(modules, list) or not modules or not all(isinstance(x, str) and x.strip() for x in modules):
                    raise ValueError(f'{label}.python_forbidden_imports[{rno}].modules: nonempty list of dotted module names required')
                if not isinstance(allows, list):
                    raise ValueError(f'{label}.python_forbidden_imports[{rno}].allow_files: expected list')
                allows = [clean_rel(x, 'allow_files[]') for x in allows]
                if canonical not in allows:
                    errors.append(f'{label}: canonical owner {canonical} is not explicitly allowed in Python import rule {rno}')
                for allow_file in allows:
                    if not (root / allow_file).is_file():
                        errors.append(f'{label}: allowed importer file missing: {allow_file}')
                rules.append((modules, set(allows)))
            normalized_caps.append((ident, canonical, globs, consumers, rules))
        except ValueError as exc:
            errors.append(str(exc))
    return errors, normalized_caps


def imports_in_python(source, filename):
    """Return (module references, unresolved import descriptions) from AST."""
    tree = ast.parse(source, filename=filename)
    path = PurePosixPath(filename)
    package = '.'.join(path.with_suffix('').parts[:-1])
    found = []
    unresolved = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ''
            if node.level:
                try:
                    base = importlib.util.resolve_name('.' * node.level + base, package)
                except (ImportError, ValueError):
                    unresolved.append(f'{filename}:{node.lineno} relative import unresolved')
                    continue
            if base:
                found.append((base, node.lineno))
            for alias in node.names:
                if alias.name != '*':
                    found.append((f'{base}.{alias.name}' if base else alias.name, node.lineno))
    return found, unresolved


def check_imports(root, normalized_caps):
    failures = []
    python_files = sorted(root.rglob('*.py'))
    # Exclude virtualenvs, build outputs, git trees, and known generated directories.
    exclusions = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.tox', 'dist', 'build'}
    python_files = [p for p in python_files if not set(p.relative_to(root).parts).intersection(exclusions)]
    for path in python_files:
        rel = path.relative_to(root).as_posix()
        # Avoid indexing the installed skill source itself as product code.
        if rel.startswith(('.claude/skills/', '.agents/skills/')):
            continue
        try:
            import_names, unresolved = imports_in_python(path.read_text(encoding='utf-8'), rel)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            failures.append(f'Cannot parse Python source {rel}: {exc}')
            continue
        # Relative imports that cannot be analyzed must never become silent PASS.
        failures.extend(unresolved)
        for cap_id, _, _, _, rules in normalized_caps:
            for modules, allowed in rules:
                if rel in allowed:
                    continue
                for name, line in import_names:
                    for forbidden in modules:
                        if name == forbidden or name.startswith(forbidden + '.'):
                            failures.append(f'{cap_id}: FORBIDDEN IMPORT {rel}:{line} -> {name} (owner-only module: {forbidden})')
                            break
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'doctor'], help='doctor validates inventory; check also enforces Python import restrictions')
    parser.add_argument('--repo', default='.', help='repository root')
    parser.add_argument('--config', default='architecture/canonical-contracts.json', help='repo-relative manifest path')
    args = parser.parse_args(argv)
    root = Path(args.repo).resolve()
    if not root.is_dir():
        print(f'ERROR: nonexistent repository directory: {root}', file=sys.stderr)
        return 2
    try:
        config = get_config(root, args.config)
        errors, caps = validate(root, config)
        if args.command == 'check':
            errors.extend(check_imports(root, caps))
    except ValueError as exc:
        print(f'NOT VERIFIED: {exc}', file=sys.stderr)
        return 2
    for error in errors:
        print(f'FAIL: {error}', file=sys.stderr)
    if errors:
        print(f'FAIL: {len(errors)} architecture contract issue(s); this is not a semantic or runtime proof.', file=sys.stderr)
        return 1
    print(f'PASS: {len(caps)} manifest capability/capabilities validated; '
          f'{"Python AST import checks run" if args.command == "check" else "file inventory validated"}.')
    print('SCOPE: route registry enumeration, JS/TS imports, runtime canonical invocation, '
          'golden behavior contracts and human approval must be checked separately.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
