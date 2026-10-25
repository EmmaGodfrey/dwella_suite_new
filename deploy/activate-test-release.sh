#!/bin/sh
set -eu

target=${1:?'Staging deployment target path is required'}
release="${target}.release"
previous="${target}.previous"
shared="${target}.shared"
compose_file="deploy/docker-compose.test.yml"

test -f "${release}/.env.test"
mkdir -p "${shared}/data/media"

if [ -d "${target}/data" ] && [ ! -L "${target}/data" ]; then
  cp -a "${target}/data/." "${shared}/data/"
fi

rm -rf "${release}/data"
ln -s "${shared}/data" "${release}/data"

(
  cd "${release}"
  docker compose --env-file .env.test -f "${compose_file}" build
)

# The new backend migrates on start, so dump the live database first. A failed
# dump stops the deployment before anything is switched.
if [ -d "${target}" ] && (
  cd "${target}"
  docker compose --env-file .env.test -f "${compose_file}" ps --status running --services | grep -qx postgres
); then
  mkdir -p "${shared}/data/backups"
  dump="${shared}/data/backups/pre-deploy-$(date -u +%Y%m%dT%H%M%SZ).dump"
  (
    cd "${target}"
    docker compose --env-file .env.test -f "${compose_file}" exec -T postgres \
      sh -c 'pg_dump -Fc --no-owner -U "$POSTGRES_USER" "$POSTGRES_DB"'
  ) > "${dump}.tmp"
  mv "${dump}.tmp" "${dump}"
  ls -1t "${shared}"/data/backups/pre-deploy-*.dump | tail -n +11 | xargs -r rm -f
fi

rm -rf "${previous}"
if [ -d "${target}" ]; then
  mv "${target}" "${previous}"
fi
mv "${release}" "${target}"

if ! (
  cd "${target}"
  docker compose --env-file .env.test -f "${compose_file}" up -d --remove-orphans
); then
  failed="${target}.failed"
  rm -rf "${failed}"
  mv "${target}" "${failed}"
  if [ -d "${previous}" ]; then
    mv "${previous}" "${target}"
    cd "${target}"
    docker compose --env-file .env.test -f "${compose_file}" up -d --remove-orphans
  fi
  exit 1
fi

rm -rf "${previous}"
docker image prune -f >/dev/null
