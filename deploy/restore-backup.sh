#!/bin/sh
# Restore a database dump made by the backup service or a pre-deploy backup.
#   deploy/restore-backup.sh prod data/backups/db-2026-11-20.dump
#   deploy/restore-backup.sh test data/backups/pre-deploy-20261120T060000Z.dump
# Run from the deployed release directory. It stops the app, replaces the
# database contents with the dump, then starts the app again. Media archives
# are restored separately: tar -xzf data/backups/media-<day>.tar.gz -C data/media
set -eu

environment=${1:?"Use prod or test"}
dump=${2:?"Path to the .dump file is required"}
case "${environment}" in
  prod) env_file=.env.prod; compose_file=deploy/docker-compose.prod.yml ;;
  test) env_file=.env.test; compose_file=deploy/docker-compose.test.yml ;;
  *) echo "Use prod or test" >&2; exit 1 ;;
esac
test -f "${dump}"
compose() { docker compose --env-file "${env_file}" -f "${compose_file}" "$@"; }

# Reject a bad archive before stopping anything. The restore itself is atomic.
compose exec -T postgres pg_restore --list < "${dump}" >/dev/null

printf 'Replace the %s database with %s? Type RESTORE to continue: ' "${environment}" "${dump}"
read -r answer
[ "${answer}" = "RESTORE" ] || { echo "Cancelled."; exit 1; }

compose stop backend scheduler
trap 'compose up -d backend scheduler' EXIT
compose exec -T postgres sh -c \
  'pg_restore --clean --if-exists --no-owner --single-transaction -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < "${dump}"
compose up -d backend scheduler
trap - EXIT
echo "Restored ${dump}."
