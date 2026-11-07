import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'webmin_boundary', Path(__file__).resolve().parents[1] / 'restrict-webmin.py',
)
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)


class WebminBoundaryTests(unittest.TestCase):
    def test_removes_wildcard_ipv6_extra_sockets_without_changing_tls_or_login_options(self):
        original = b'port=10000\nssl=1\nkeyfile=/private/key\nbind=*\nbind=::\nallow=all\nsockets=*:10001 ::1:10002\nlisten=10000\n'
        changed = boundary.restricted(original)
        self.assertIn(b'ssl=1\nkeyfile=/private/key\n', changed)
        self.assertEqual(changed.count(b'bind='), 1)
        self.assertIn(b'bind=127.0.0.1\nallow=127.0.0.1\nsockets=\nlisten=0\n', changed)
        self.assertEqual(boundary.restricted(changed), changed)

    def test_unknown_port_and_missing_ssh_tuple_fail_closed(self):
        with self.assertRaises(ValueError):
            boundary.restricted(b'port=10001\n')
        for value in ['', 'not an ssh tuple', 'bad 123 127.0.0.1 22']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                boundary.connection(value)

    def test_public_listener_or_mixed_ipv6_listener_is_rejected(self):
        good = 'LISTEN 0 4096 127.0.0.1:10000 0.0.0.0:*\n'
        self.assertTrue(boundary.listeners_safe(good))
        for value in ['', good + 'LISTEN 0 4096 [::]:10000 [::]:*\n',
                      'LISTEN 0 4096 0.0.0.0:10000 0.0.0.0:*\n']:
            self.assertFalse(boundary.listeners_safe(value))

    def test_rollback_restores_saved_file_and_leaves_confirmed_changes_alone(self):
        with tempfile.TemporaryDirectory() as folder:
            state = Path(folder) / 'state'
            state.mkdir()
            config = Path(folder) / 'miniserv.conf'
            original = b'port=10000\nssl=1\n'
            changed = boundary.restricted(original)
            config.write_bytes(changed)
            (state / 'original.conf').write_bytes(original)
            metadata = {'original_hash':boundary.digest(original),
                        'restricted_hash':boundary.digest(changed),'mode':0o600,'confirmed':False}
            (state / 'state.json').write_text(json.dumps(metadata))
            with patch.object(boundary,'STATE',state), patch.object(boundary,'CONFIG',config), \
                    patch.object(boundary,'run',return_value=SimpleNamespace(stdout='')):
                boundary.rollback()
                self.assertEqual(config.read_bytes(),original)
                metadata['confirmed']=True
                (state / 'state.json').write_text(json.dumps(metadata))
                config.write_bytes(changed)
                boundary.rollback()
                self.assertEqual(config.read_bytes(),changed)

    def test_confirmation_requires_a_new_ssh_connection(self):
        value='192.0.2.1 12345 192.0.2.2 22'
        with tempfile.TemporaryDirectory() as folder:
            state=Path(folder)
            (state / 'state.json').write_text(json.dumps({'connection':boundary.connection(value)}))
            with patch.object(boundary,'STATE',state), self.assertRaises(ValueError):
                boundary.confirm(value)
