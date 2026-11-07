"""Independent public HTTPS checks. No authentication, response bodies or personal data in logs."""
import json
import time
from urllib.request import Request, urlopen

TARGETS = [
    ('api', 'https://api.dwella.properties/api/health/', b'"status"'),
    ('application', 'https://app.dwella.properties/', b'Dwella'),
    ('website', 'https://dwella.properties/', b'Dwella'),
]


def check(name, url, marker):
    started = time.monotonic()
    for attempt in range(2):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'Dwella-Uptime/1.0'}), timeout=10) as response:
                body = response.read(262144)
                good = response.status == 200 and marker in body
                if good and name == 'api':
                    data = json.loads(body)
                    good = data.get('status') == 'ok' or data.get('response_data', {}).get('status') == 'ok'
                if good:
                    return {'name': name, 'healthy': True,
                            'elapsed_ms': round((time.monotonic()-started)*1000)}
        except Exception:
            pass
        if attempt == 0:
            time.sleep(2)
    return {'name': name, 'healthy': False}


if __name__ == '__main__':
    results = [check(*target) for target in TARGETS]
    print(json.dumps({'checks': results}))
    raise SystemExit(0 if all(row['healthy'] for row in results) else 1)
