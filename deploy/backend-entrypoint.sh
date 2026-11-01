#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  python manage.py createsuperuser --noinput 2>/dev/null || true
fi

# Threaded workers: a request waiting on Lenco, SMTP or the database no longer
# blocks a whole process. Concurrency is workers x threads (default 3 x 4 = 12).
# Each thread may hold up to two PostgreSQL connections (default + email quota),
# so keep workers x threads x 2 well under PostgreSQL max_connections (100).
# Recycling workers bounds slow memory growth; jitter avoids restarting together.
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --worker-class gthread \
  --workers "${GUNICORN_WORKERS:-3}" \
  --threads "${GUNICORN_THREADS:-4}" \
  --max-requests "${GUNICORN_MAX_REQUESTS:-2000}" \
  --max-requests-jitter "${GUNICORN_MAX_REQUESTS_JITTER:-200}" \
  --keep-alive "${GUNICORN_KEEP_ALIVE:-5}" \
  --graceful-timeout "${GUNICORN_GRACEFUL_TIMEOUT:-30}" \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --access-logformat '%(h)s %(l)s %(u)s %(t)s "%(m)s %(U)s %(H)s" %(s)s %(b)s' \
  --error-logfile -

