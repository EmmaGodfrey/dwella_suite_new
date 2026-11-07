#!/usr/bin/env python3
"""Root-only Ubuntu hardening with an SSH lockout rollback timer.

Install a reviewed copy under /root before applying. Firewall changes and reboot
are deliberately separate: this host also serves other applications.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

STATE = Path("/var/lib/dwella-hardening")
UNIT = "dwella-hardening-rollback"
SSH = Path("/etc/ssh/sshd_config.d/00-00-dwella-hardening.conf")
JOURNAL = Path("/etc/systemd/journald.conf.d/60-dwella-bounds.conf")
SYSCTL = Path("/etc/sysctl.d/60-dwella-hardening.conf")
PARAMETERS = {
    "kernel.kptr_restrict": "2", "kernel.dmesg_restrict": "1",
    "fs.protected_hardlinks": "1", "fs.protected_symlinks": "1",
    "net.ipv4.conf.all.accept_redirects": "0",
    "net.ipv4.conf.default.accept_redirects": "0",
    "net.ipv4.conf.all.send_redirects": "0",
    "net.ipv4.conf.default.send_redirects": "0",
    "net.ipv4.tcp_syncookies": "1",
    "net.ipv6.conf.all.accept_redirects": "0",
    "net.ipv6.conf.default.accept_redirects": "0",
}
SSH_SETTINGS = {
    "permitrootlogin": "no", "passwordauthentication": "no",
    "kbdinteractiveauthentication": "no", "pubkeyauthentication": "yes",
    "permitemptypasswords": "no", "x11forwarding": "no",
    "maxauthtries": "3", "logingracetime": "30", "maxstartups": "10:30:60",
}


def run(args, *, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check, timeout=45)


def connection(value):
    parts = value.split()
    if len(parts) != 4 or not parts[1].isdigit() or not parts[3].isdigit():
        raise ValueError("Run from SSH and pass --connection \"$SSH_CONNECTION\"")
    return parts


def assert_effective(text):
    settings = dict(line.split(None, 1) for line in text.splitlines() if " " in line)
    wrong = [key for key, value in SSH_SETTINGS.items() if settings.get(key) != value]
    if wrong:
        raise ValueError("Existing SSH configuration overrides: " + ", ".join(wrong))


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".dwella-tmp")
    temporary.write_text(content)
    temporary.chmod(0o600 if path == STATE / "state.json" else 0o644)
    temporary.replace(path)


def rollback():
    state = json.loads((STATE / "state.json").read_text())
    if state["status"] != "pending":
        return
    for name, content in state["files"].items():
        path = Path(name)
        if content is None:
            path.unlink(missing_ok=True)
        else:
            write(path, content)
    for key, value in state["sysctls"].items():
        run(["sysctl", "-w", f"{key}={value}"])
    run(["/usr/sbin/sshd", "-t"])
    run(["systemctl", "reload", "ssh"])
    run(["systemctl", "restart", "systemd-journald"])
    state["status"] = "rolled-back"
    write(STATE / "state.json", json.dumps(state))
    print("Previous SSH, kernel and journal settings restored")


def apply(args):
    import pwd

    client = connection(args.connection)
    executable = Path(__file__).resolve()
    if executable.stat().st_uid != 0 or executable.stat().st_mode & 0o022 or executable.parent != Path("/root"):
        raise ValueError("Install the reviewed script root-owned with mode 0700 under /root first")
    account = pwd.getpwnam(args.ssh_user)
    if account.pw_uid == 0:
        raise ValueError("A non-root recovery SSH account is required")
    authorized = Path(account.pw_dir) / ".ssh/authorized_keys"
    if not authorized.is_file() or not authorized.read_text().strip():
        raise ValueError("Recovery account must have an authorized SSH key")
    run(["/usr/sbin/sshd", "-t"])
    STATE.mkdir(mode=0o700, exist_ok=True)
    STATE.chmod(0o700)
    state_file = STATE / "state.json"
    if state_file.exists() and json.loads(state_file.read_text())["status"] == "pending":
        raise ValueError("An unconfirmed change already exists; confirm or roll back first")
    state = {
        "status": "pending", "time": int(time.time()), "connection": args.connection,
        "files": {str(p): p.read_text() if p.exists() else None for p in (SSH, JOURNAL, SYSCTL)},
        "sysctls": {key: run(["sysctl", "-n", key]).stdout.strip() for key in PARAMETERS},
    }
    write(state_file, json.dumps(state))
    run(["systemctl", "reset-failed", UNIT + ".service"], check=False)
    run(["systemd-run", "--unit=" + UNIT, "--on-active=180s", "--timer-property=AccuracySec=1s", sys.executable, str(executable), "rollback"])
    try:
        write(SSH, "# Managed by Dwella host hardening; key authentication required.\n" + "\n".join(f"{key} {value}" for key, value in SSH_SETTINGS.items()) + "\n")
        run(["/usr/sbin/sshd", "-t"])
        for user in (args.ssh_user, "root"):
            effective = run(["/usr/sbin/sshd", "-T", "-C", f"user={user},addr={client[0]},host={client[0]}"]).stdout
            assert_effective(effective)
        write(SYSCTL, "# Preserve forwarding, bridge networking and IPv6 autoconfiguration.\n" + "\n".join(f"{key} = {value}" for key, value in PARAMETERS.items()) + "\n")
        for key, value in PARAMETERS.items():
            run(["sysctl", "-w", f"{key}={value}"])
        write(JOURNAL, "[Journal]\nSystemMaxUse=512M\nRuntimeMaxUse=128M\nMaxRetentionSec=14day\n")
        run(["systemctl", "restart", "systemd-journald"])
        run(["systemctl", "reload", "ssh"])
    except Exception:
        rollback()
        raise
    print("Applied. Within 180 seconds, open a NEW SSH connection and run:")
    print('sudo python3 /root/harden-host.py confirm --connection "$SSH_CONNECTION"')
    print("If the new login fails, these changes automatically roll back.")


def confirm(args):
    connection(args.connection)
    state = json.loads((STATE / "state.json").read_text())
    if state["status"] != "pending" or state["connection"] == args.connection:
        raise ValueError("Confirm from a fresh SSH connection while a change is pending")
    # Mark confirmed before cancelling the timer; a queued rollback then does nothing.
    state["status"] = "confirmed"
    write(STATE / "state.json", json.dumps(state))
    run(["systemctl", "stop", UNIT + ".timer"], check=False)
    print("Fresh SSH access confirmed; rollback timer cancelled")


def audit():
    for label, command in [
        ("Firewall", ["ufw", "status", "verbose"]),
        ("Forwarded Docker traffic", ["iptables", "-S", "DOCKER-USER"]),
        ("SSH", ["/usr/sbin/sshd", "-T"]),
        ("Failed units", ["systemctl", "--failed", "--no-pager"]),
        ("Security updates", ["systemctl", "is-active", "unattended-upgrades"]),
    ]:
        result = run(command, check=False)
        output = result.stdout
        if label == "SSH":
            output = "\n".join(line for line in output.splitlines() if line.split()[0] in SSH_SETTINGS)
        print(f"{label} (exit {result.returncode}):\n{output}")
    pid = run(["systemctl", "show", "nginx", "-p", "MainPID", "--value"]).stdout.strip()
    def digest(path):
        result = hashlib.sha256()
        with Path(path).open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                result.update(chunk)
        return result.hexdigest()
    print("Nginx running binary matches installed:", digest(f"/proc/{pid}/exe") == digest("/usr/sbin/nginx"))
    print("Reboot required:", Path("/var/run/reboot-required").exists())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["audit", "apply", "confirm", "rollback"])
    parser.add_argument("--connection", default="")
    parser.add_argument("--ssh-user", default="emmanuel")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run through sudo; never share the sudo password with an agent")
    import fcntl

    STATE.mkdir(mode=0o700, exist_ok=True)
    # Serialize confirmation and the timed rollback so they cannot race.
    lock = (STATE / ".lock").open("w")
    fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
    try:
        if args.action == "apply":
            apply(args)
        elif args.action == "confirm":
            confirm(args)
        elif args.action == "rollback":
            rollback()
        else:
            audit()
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f"Hardening stopped: {type(exc).__name__}. Check the local administrator terminal; no credentials printed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
