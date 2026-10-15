import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / 'scripts' / 'arch_guard.py'
HOOK = SKILL / 'scripts' / 'claude_protect.py'


def fixture(root):
    files = {
        'src/domain/orders/normalize.py': 'from src.domain.orders.mappers import mapping\n',
        'src/domain/orders/mappers.py': 'mapping = object()\n',
        'src/domain/orders/rules.py': 'RULE = 1\n',
        'src/api/orders/create_route.py': 'from src.domain.orders.normalize import normalize\n',
        'src/workers/order_ingest.py': 'import src.domain.orders.normalize\n',
    }
    for name, content in files.items():
        dest = root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
    manifest = {
        'version': 1,
        'capabilities': [{
            'id': 'order-normalization',
            'canonical': 'src/domain/orders/normalize.py',
            'consumer_globs': ['src/api/orders/*_route.py', 'src/workers/order_*.py'],
            'consumers': ['src/api/orders/create_route.py', 'src/workers/order_ingest.py'],
            'python_forbidden_imports': [{
                'modules': ['src.domain.orders.mappers', 'src.domain.orders.rules'],
                'allow_files': ['src/domain/orders/normalize.py']
            }],
        }]
    }
    cfg = root / 'architecture/canonical-contracts.json'
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(manifest))
    return cfg


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cfg = fixture(self.root)

    def check(self, command='check'):
        return subprocess.run([sys.executable, str(SCRIPT), command, '--repo', str(self.root)], capture_output=True, text=True)

    def test_positive_path(self):
        self.assertEqual(self.check().returncode, 0)

    def test_unregistered_new_consumer_fails(self):
        (self.root / 'src/api/orders/update_route.py').write_text('pass\n')
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('UNREGISTERED CONSUMER', r.stderr)

    def test_bypass_import_fails(self):
        (self.root / 'src/api/orders/create_route.py').write_text('from src.domain.orders.mappers import mapping\n')
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn('FORBIDDEN IMPORT', r.stderr)

    def test_relative_import_fails(self):
        dest = self.root / 'src/domain/orders/sibling.py'
        dest.write_text('from .mappers import mapping\n')
        r = self.check()
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('FORBIDDEN IMPORT', r.stderr)

    def test_missing_manifest_not_verified(self):
        self.cfg.unlink()
        r = self.check()
        self.assertEqual(r.returncode, 2)
        self.assertIn('NOT VERIFIED', r.stderr)

    def test_empty_inventory_fails(self):
        m = json.loads(self.cfg.read_text())
        m['capabilities'][0]['consumer_globs'] = ['src/api/missing/*.py']
        self.cfg.write_text(json.dumps(m))
        self.assertEqual(self.check().returncode, 1)

    def test_duplicate_capabilities_fails(self):
        m = json.loads(self.cfg.read_text())
        m['capabilities'].append(m['capabilities'][0])
        self.cfg.write_text(json.dumps(m))
        self.assertEqual(self.check().returncode, 1)

    def test_hook_requires_approval_for_manifest_edit(self):
        env = os.environ.copy()
        env['CLAUDE_PROJECT_DIR'] = str(self.root)
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({
            'tool_name': 'Edit', 'tool_input': {'file_path': str(self.cfg)}
        }), capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout)['hookSpecificOutput']['permissionDecision'], 'ask')

    def test_hook_skips_regular_code(self):
        env = os.environ.copy()
        env['CLAUDE_PROJECT_DIR'] = str(self.root)
        r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps({
            'tool_name': 'Edit', 'tool_input': {'file_path': 'src/api/orders/create_route.py'}
        }), capture_output=True, text=True, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, '')

if __name__ == '__main__':
    unittest.main()
