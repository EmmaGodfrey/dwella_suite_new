#!/usr/bin/env python3
"""Validate resolved Compose JSON without printing environment values."""
import json
import sys


def positive_integer(value):
    # Compose releases serialize byte limits as either integers or decimal strings.
    return not isinstance(value, bool) and str(value).isdigit() and int(value) > 0


def violations(config):
    errors = []
    services = config.get("services", {})
    if not services:
        return ["No services found"]
    unprivileged = {"backend", "scheduler", "signing-mailer", "payments-worker",
                    "whatsapp-worker", "backup", "db-gateway"}
    for name, service in services.items():
        def reject(condition, message):
            if condition:
                errors.append(f"{name}: {message}")

        reject(service.get("privileged", False), "privileged containers are forbidden")
        reject(service.get("pid") == "host" or service.get("ipc") == "host", "host process namespaces are forbidden")
        security = {s.replace("=", ":") for s in service.get("security_opt", [])}
        reject("no-new-privileges:true" not in security, "no-new-privileges is required")
        reject(not positive_integer(service.get("mem_limit")), "a positive memory limit is required")
        reject(not positive_integer(service.get("pids_limit")), "a positive process limit is required")
        logging = service.get("logging", {})
        options = logging.get("options", {})
        reject(logging.get("driver") != "json-file" or options.get("max-size") != "10m" or str(options.get("max-file")) != "5", "bounded 10m x 5 operational logs are required")
        if name in unprivileged:
            reject("ALL" not in service.get("cap_drop", []), "all capabilities must be dropped")
            reject(bool(service.get("cap_add")), "additional capabilities are forbidden")
        if name == "frontend":
            reject("ALL" not in service.get("cap_drop", []), "default capabilities must be dropped")
            reject(set(service.get("cap_add", [])) - {"CHOWN", "SETUID", "SETGID", "NET_BIND_SERVICE"}, "unexpected Nginx capability")
        reject(service.get("network_mode") == "host" and name != "db-gateway", "host networking is restricted to the reviewed database gateway")
        for port in service.get("ports", []):
            reject(port.get("host_ip") not in {"127.0.0.1", "::1"}, "published ports must bind to loopback")
        for mount in service.get("volumes", []):
            reject(mount.get("source") in {"/", "/var/run/docker.sock", "/run/docker.sock"}, "host root and Docker socket mounts are forbidden")
    return errors


def main():
    try:
        errors = violations(json.load(sys.stdin))
    except (ValueError, TypeError, AttributeError):
        print("Invalid resolved Compose configuration", file=sys.stderr)
        return 1
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Container runtime security policy passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
