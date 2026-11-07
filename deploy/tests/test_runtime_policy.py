import copy
import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("runtime_policy", Path(__file__).resolve().parents[1] / "check-runtime-policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class RuntimePolicyTests(unittest.TestCase):
    def setUp(self):
        self.service = {
            "mem_limit": 1024**3, "pids_limit": 256,
            "security_opt": ["no-new-privileges:true"], "cap_drop": ["ALL"],
            "logging": {"driver": "json-file", "options": {"max-size": "10m", "max-file": "5"}},
            "ports": [{"target": 8000, "published": "8120", "host_ip": "127.0.0.1"}],
        }

    def errors(self, **overrides):
        return policy.violations({"services": {"backend": {**copy.deepcopy(self.service), **overrides}}})

    def test_safe_backend_and_normalized_security_option(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.errors(security_opt=["no-new-privileges=true"]), [])
        self.assertEqual(self.errors(mem_limit="1073741824"), [])

    def test_rejects_privilege_escalation(self):
        for overrides in [{"privileged": True}, {"cap_drop": []}, {"cap_add": ["SYS_ADMIN"]}, {"security_opt": []}, {"pid": "host"}, {"ipc": "host"}, {"network_mode": "host"}]:
            with self.subTest(overrides=overrides):
                self.assertTrue(self.errors(**overrides))

    def test_rejects_unbounded_resources_and_logs(self):
        for overrides in [{"mem_limit": 0}, {"mem_limit": -1}, {"mem_limit": True}, {"mem_limit": "unlimited"}, {"pids_limit": -1}, {"logging": {}}, {"logging": {"driver": "json-file", "options": {"max-size": "0", "max-file": "5"}}}]:
            with self.subTest(overrides=overrides):
                self.assertTrue(self.errors(**overrides))

    def test_rejects_public_ports_ipv4_and_ipv6(self):
        for host in [None, "0.0.0.0", "::", "192.0.2.1"]:
            with self.subTest(host=host):
                self.assertTrue(self.errors(ports=[{"host_ip": host, "published": "8120"}]))
        self.assertEqual(self.errors(ports=[{"host_ip": "::1", "published": "8120"}]), [])

    def test_rejects_host_control_mounts(self):
        for source in ["/", "/var/run/docker.sock", "/run/docker.sock"]:
            with self.subTest(source=source):
                self.assertTrue(self.errors(volumes=[{"source": source}]))

    def test_nginx_has_only_needed_capabilities(self):
        frontend = {**self.service, "cap_add": ["CHOWN", "SETUID", "SETGID", "NET_BIND_SERVICE"]}
        self.assertEqual(policy.violations({"services": {"frontend": frontend}}), [])
        frontend["cap_add"].append("SYS_ADMIN")
        self.assertTrue(policy.violations({"services": {"frontend": frontend}}))

    def test_empty_config_fails_closed(self):
        self.assertTrue(policy.violations({}))

    def test_whatsapp_worker_must_drop_all_capabilities(self):
        worker = {**self.service, "volumes": [{"source": "/srv/test/media", "target": "/app/backend/media"}]}
        self.assertEqual(policy.violations({"services": {"whatsapp-worker": worker}}), [])
        unsafe = {**worker, "cap_drop": []}
        self.assertTrue(policy.violations({"services": {"whatsapp-worker": unsafe}}))

    def test_maintenance_profile_cannot_gain_container_capabilities(self):
        self.assertEqual(policy.violations({"services": {"maintenance": self.service}}), [])
        unsafe = {**self.service, "cap_drop": []}
        self.assertTrue(policy.violations({"services": {"maintenance": unsafe}}))

    def test_whatsapp_worker_requires_shared_media(self):
        self.assertTrue(policy.violations({"services": {"whatsapp-worker": self.service}}))


if __name__ == "__main__":
    unittest.main()
