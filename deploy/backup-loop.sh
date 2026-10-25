#!/bin/sh
# Nightly backups inside the backup container: a compressed database dump and a
# media archive per day, verified before they replace anything, pruned after
# BACKUP_KEEP_DAYS. These stay on this server; copy /backups off-host as well.
set -u

keep_days=${BACKUP_KEEP_DAYS:-14}
backup_hour=${BACKUP_HOUR_UTC:-0}

backup_today() {
  day=$(date -u +%Y-%m-%d)
  dump="/backups/db-${day}.dump"
  media="/backups/media-${day}.tar.gz"
  if [ ! -f "${dump}" ]; then
    if pg_dump -Fc --no-owner -f "${dump}.tmp" && pg_restore --list "${dump}.tmp" >/dev/null; then
      mv "${dump}.tmp" "${dump}"
      echo "$(date -u +%FT%TZ) database backup ${dump}"
    else
      rm -f "${dump}.tmp"
      echo "$(date -u +%FT%TZ) database backup FAILED" >&2
    fi
  fi
  if [ ! -f "${media}" ] && [ -d /media ]; then
    if tar -czf "${media}.tmp" -C /media . && tar -tzf "${media}.tmp" >/dev/null; then
      mv "${media}.tmp" "${media}"
      echo "$(date -u +%FT%TZ) media backup ${media}"
    else
      rm -f "${media}.tmp"
      echo "$(date -u +%FT%TZ) media backup FAILED" >&2
    fi
  fi
  find /backups -maxdepth 1 \( -name 'db-*.dump' -o -name 'media-*.tar.gz' \) \
    -mtime +"${keep_days}" -delete
}

mkdir -p /backups
while true; do
  if [ "$(date -u +%H)" -ge "${backup_hour}" ]; then
    backup_today
  fi
  sleep 900
done
