import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("host_hardening", Path(__file__).resolve().parents[1] / "harden-host.py")
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class HostHardeningTests(unittest.TestCase):
    def test_connection_requires_an_ssh_tuple(self):
        for value in ["", "198.51.100.1", "198.51.100.1 x 192.0.2.1 22"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                host.connection(value)
        self.assertEqual(host.connection("198.51.100.1 50123 192.0.2.1 22")[3], "22")

    def test_effective_configuration_rejects_match_override(self):
        effective = "\n".join(f"{k} {v}" for k, v in host.SSH_SETTINGS.items())
        host.assert_effective(effective)
        with self.assertRaises(ValueError):
            host.assert_effective(effective.replace("passwordauthentication no", "passwordauthentication yes"))
        with self.assertRaises(ValueError):
            host.assert_effective("")

    def test_rollback_restores_changed_files_and_removes_new_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, created = root / "original.conf", root / "created.conf"
            original.write_text("changed")
            created.write_text("new")
            state = {"status": "pending", "files": {str(original): "before", str(created): None}, "sysctls": {"kernel.kptr_restrict": "1"}}
            (root / "state.json").write_text(json.dumps(state))
            with patch.object(host, "STATE", root), patch.object(host, "run") as run:
                host.rollback()
            self.assertEqual(original.read_text(), "before")
            self.assertFalse(created.exists())
            self.assertEqual(json.loads((root / "state.json").read_text())["status"], "rolled-back")
            run.assert_any_call(["systemctl", "reload", "ssh"])

    def test_confirmed_state_is_not_rolled_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "state.json").write_text('{"status":"confirmed"}')
            with patch.object(host, "STATE", root), patch.object(host, "run") as run:
                host.rollback()
            run.assert_not_called()

    def test_confirmation_requires_a_new_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            connection = "198.51.100.1 50123 192.0.2.1 22"
            (root / "state.json").write_text(json.dumps({"status": "pending", "connection": connection}))
            args = type("Args", (), {"connection": connection})()
            with patch.object(host, "STATE", root), self.assertRaises(ValueError):
                host.confirm(args)
            args.connection = "198.51.100.1 50124 192.0.2.1 22"
            with patch.object(host, "STATE", root), patch.object(host, "run"):
                host.confirm(args)
            self.assertEqual(json.loads((root / "state.json").read_text())["status"], "confirmed")
