#!/usr/bin/env python3
"""Root-only Webmin loopback restriction with a five-minute rollback timer."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import subprocess

CONFIG = Path('/etc/webmin/miniserv.conf')
STATE = Path('/var/lib/dwella-webmin-boundary')
SCRIPT = Path('/root/dwella-restrict-webmin.py')
UNIT = 'dwella-webmin-rollback'
SETTINGS = {'bind': '127.0.0.1', 'allow': '127.0.0.1', 'sockets': '', 'listen': '0'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def connection(value):
    parts = value.split()
    if len(parts) != 4 or not parts[1].isdigit() or not parts[3].isdigit():
        raise ValueError('Pass the current SSH_CONNECTION tuple.')
    ipaddress.ip_address(parts[0])
    ipaddress.ip_address(parts[2])
    return digest(value.encode())


def restricted(raw):
    text = raw.decode('utf-8')
    values = dict(line.split('=', 1) for line in text.splitlines()
                  if '=' in line and not line.lstrip().startswith('#'))
    if values.get('port') != '10000':
        raise ValueError('Review the configured Webmin port before using this tool.')
    lines = [line for line in text.splitlines()
             if line.split('=', 1)[0].strip() not in SETTINGS]
    return ('\n'.join([*lines, *(f'{key}={value}' for key, value in SETTINGS.items()), ''])).encode()


def listeners_safe(text):
    rows = [line.split() for line in text.splitlines() if line.strip()]
    return bool(rows) and all(len(row) >= 4 and row[3] == '127.0.0.1:10000' for row in rows)


def run(args, *, check=True):
    return subprocess.run(args, check=check, capture_output=True, text=True, timeout=30)


def write(path, raw, mode=0o600):
    temporary = path.with_name(path.name + '.dwella-tmp')
    temporary.write_bytes(raw)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def verify():
    run(['systemctl', 'is-active', '--quiet', 'webmin'])
    result = run(['ss', '-lntH', 'sport = :10000'])
    if not listeners_safe(result.stdout):
        raise ValueError('Webmin is not restricted to the expected loopback listener.')


def rollback():
    path = STATE / 'state.json'
    state = json.loads(path.read_text())
    if state.get('confirmed') or state.get('rolled_back'):
        return
    current = digest(CONFIG.read_bytes())
    if current not in {state['original_hash'], state['restricted_hash']}:
        raise ValueError('Webmin config changed independently; restore requires operator review.')
    write(CONFIG, (STATE / 'original.conf').read_bytes(), state['mode'])
    run(['systemctl', 'restart', 'webmin'])
    state['rolled_back'] = True
    write(path, json.dumps(state).encode())
    run(['systemctl', 'stop', UNIT + '.timer'], check=False)
    print('Original Webmin configuration restored.')


def apply(ssh_connection):
    stamp = connection(ssh_connection)
    if Path(__file__).resolve() != SCRIPT or SCRIPT.stat().st_uid != 0 or SCRIPT.stat().st_mode & 0o022:
        raise ValueError('Install the reviewed script root-owned under /root first.')
    if (STATE / 'state.json').exists():
        old = json.loads((STATE / 'state.json').read_text())
        if not old.get('confirmed') and not old.get('rolled_back'):
            raise ValueError('Confirm or roll back the pending Webmin change first.')
    raw = CONFIG.read_bytes()
    changed = restricted(raw)
    if raw == changed:
        verify()
        print('Webmin is already restricted to loopback.')
        return
    run(['systemctl', 'is-active', '--quiet', 'webmin'])
    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE, 0o700)
    write(STATE / 'original.conf', raw)
    state = {'connection': stamp, 'original_hash': digest(raw), 'restricted_hash': digest(changed),
             'mode': CONFIG.stat().st_mode & 0o777, 'confirmed': False}
    write(STATE / 'state.json', json.dumps(state).encode())
    run(['systemd-run', '--unit=' + UNIT, '--on-active=5m', '/usr/bin/python3', str(SCRIPT), 'rollback'])
    try:
        write(CONFIG, changed, state['mode'])
        run(['systemctl', 'restart', 'webmin'])
        verify()
    except Exception:
        rollback()
        raise
    print('Webmin now listens on loopback. Verify the SSH tunnel, then confirm from a fresh SSH connection within five minutes.')


def confirm(ssh_connection):
    state = json.loads((STATE / 'state.json').read_text())
    if state.get('rolled_back') or connection(ssh_connection) == state['connection']:
        raise ValueError('Use a fresh SSH connection after verifying the Webmin tunnel.')
    if digest(CONFIG.read_bytes()) != state['restricted_hash']:
        raise ValueError('The expected Webmin configuration changed.')
    verify()
    state['confirmed'] = True
    write(STATE / 'state.json', json.dumps(state).encode())
    run(['systemctl', 'stop', UNIT + '.timer'], check=False)
    print('Webmin loopback restriction confirmed; rollback timer cancelled.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['plan', 'apply', 'confirm', 'rollback'])
    parser.add_argument('--connection', default='')
    args = parser.parse_args()
    if getattr(os, 'geteuid', lambda: -1)() != 0:
        raise SystemExit('Run through legitimate sudo/root access.')
    # Serialise confirm/rollback so an expiring timer cannot restore an old
    # public configuration after a successful confirmation.
    import fcntl

    STATE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE, 0o700)
    try:
        with (STATE / 'operation.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if args.operation == 'plan':
                restricted(CONFIG.read_bytes())
                print(json.dumps({'port': 10000, 'settings': SETTINGS, 'rollback_minutes': 5}))
            elif args.operation == 'apply':
                apply(args.connection)
            elif args.operation == 'confirm':
                confirm(args.connection)
            else:
                rollback()
    except Exception as error:
        # miniserv.conf may contain sensitive paths/options; never print raw content.
        raise SystemExit('Webmin boundary operation failed: ' + type(error).__name__) from None


if __name__ == '__main__':
    main()
