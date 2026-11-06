import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'runtime_env', Path(__file__).resolve().parents[1] / 'prepare-runtime-env.py',
)
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


class RuntimeEnvTests(unittest.TestCase):
    def source(self):
        return '\n'.join([
            'DATABASE_URL=postgresql://migration:secret@postgres:5432/dwella',
            'APP_RUNTIME_DATABASE_URL=postgresql://dwella_runtime:' + 'x' * 40 + '@postgres:5432/dwella',
            'APP_RUNTIME_ENV_FILE=../.env.runtime',
            'POSTGRES_PASSWORD=maintenance-password',
            'POSTGRES_USER=migration',
            'DJANGO_SUPERUSER_PASSWORD=bootstrap-password',
            'APP_MIGRATION_PASSWORD=hidden',
            'APP_RUN_MIGRATIONS=true',
            'APP_ENVIRONMENT=production',
            'WHATSAPP_ACCESS_TOKEN=synthetic-provider-key',
        ])

    def test_runtime_env_excludes_maintenance_credentials_but_keeps_required_app_keys(self):
        value = runtime.render(self.source())
        self.assertNotIn('maintenance-password', value)
        self.assertNotIn('bootstrap-password', value)
        self.assertNotIn('APP_MIGRATION_', value)
        self.assertNotIn('APP_RUNTIME_DATABASE_URL=', value)
        self.assertIn('DATABASE_URL=postgresql://dwella_runtime:', value)
        self.assertIn('WHATSAPP_ACCESS_TOKEN=synthetic-provider-key', value)
        self.assertIn('APP_RUN_MIGRATIONS=false', value)

    def test_rejects_missing_or_same_role_wrong_database_and_weak_password(self):
        for change in [
            self.source().replace('APP_RUNTIME_DATABASE_URL=', 'MISSING='),
            self.source().replace('dwella_runtime:', 'migration:'),
            self.source().replace('x' * 40, 'short'),
            self.source().replace('x' * 40 + '@postgres', 'x' * 40 + '@other'),
            self.source().replace('x' * 40 + '@postgres:5432/dwella', 'x' * 40 + '@postgres:5432/other'),
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                runtime.render(change)

    def test_prepares_sibling_file_without_overwriting_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / '.env.prod', Path(folder) / '.env.runtime'
            source.write_text(self.source(), encoding='utf-8')
            runtime.prepare(source, target)
            self.assertEqual(source.read_text(), self.source())
            self.assertIn('APP_RUN_MIGRATIONS=false', target.read_text())
            with self.assertRaises(ValueError):
                runtime.prepare(source, source)
