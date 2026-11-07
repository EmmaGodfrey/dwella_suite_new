"""Derive a locked runtime env without maintenance DB or bootstrap credentials.

Values are never printed. The source stays with the migration/backup operator.
"""
import argparse
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


def render(source):
    lines = source.splitlines()
    values = {}
    for line in lines:
        if '=' in line and not line.lstrip().startswith('#'):
            key, value = line.split('=', 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    runtime = values.get('APP_RUNTIME_DATABASE_URL', '')
    if values.get('APP_RUNTIME_ENV_FILE') != '../.env.runtime':
        raise ValueError('Select the sibling runtime env explicitly in the maintenance env.')
    original = urlsplit(values.get('DATABASE_URL', ''))
    parsed = urlsplit(runtime)
    if (parsed.scheme not in {'postgres', 'postgresql'} or not parsed.username
            or len(parsed.password or '') < 32 or parsed.username == original.username
            or parsed.hostname != original.hostname or parsed.port != original.port
            or parsed.path != original.path or '\n' in runtime or '\r' in runtime):
        raise ValueError('Configure a distinct restricted runtime URL for the same database.')
    excluded = {'DATABASE_URL', 'APP_RUNTIME_DATABASE_URL', 'APP_RUN_MIGRATIONS'}
    result = []
    for line in lines:
        key = line.split('=', 1)[0].strip()
        if key in excluded or key.startswith(('POSTGRES_', 'DJANGO_SUPERUSER_', 'APP_MIGRATION_')):
            continue
        result.append(line)
    return '\n'.join([*result, f'DATABASE_URL={runtime}', 'APP_RUN_MIGRATIONS=false', ''])


def prepare(source, target):
    source, target = Path(source).resolve(), Path(target).absolute()
    if target.is_symlink() or source == target.resolve() or target.parent != source.parent:
        raise ValueError('Use a separate runtime file beside the protected source env.')
    rendered = render(source.read_text(encoding='utf-8'))
    descriptor, name = tempfile.mkstemp(prefix='.env.runtime-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as output:
            output.write(rendered)
        os.chmod(name, 0o600)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--target', required=True)
    options = parser.parse_args()
    try:
        prepare(options.source, options.target)
    except Exception:
        raise SystemExit('Runtime env preparation failed; values suppressed.') from None
    print('Restricted runtime env prepared; maintenance credentials excluded.')
