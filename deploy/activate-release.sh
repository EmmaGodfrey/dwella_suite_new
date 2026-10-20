#!/bin/sh
set -eu

target=${1:?"Deployment target path is required"}
release="${target}.release"
previous="${target}.previous"
shared="${target}.shared"
compose_file="deploy/docker-compose.prod.yml"

test -f "${release}/.env.prod"
mkdir -p "${shared}/data/media"

if [ -d "${target}/data" ] && [ ! -L "${target}/data" ]; then
  cp -a "${target}/data/." "${shared}/data/"
fi

rm -rf "${release}/data"
ln -s "${shared}/data" "${release}/data"

(
  cd "${release}"
  docker compose --env-file .env.prod -f "${compose_file}" build
)

rm -rf "${previous}"
if [ -d "${target}" ]; then
  mv "${target}" "${previous}"
fi
mv "${release}" "${target}"

if ! (
  cd "${target}"
  docker compose --env-file .env.prod -f "${compose_file}" up -d --remove-orphans
); then
  failed="${target}.failed"
  rm -rf "${failed}"
  mv "${target}" "${failed}"
  if [ -d "${previous}" ]; then
    mv "${previous}" "${target}"
    cd "${target}"
    docker compose --env-file .env.prod -f "${compose_file}" up -d --remove-orphans
  fi
  exit 1
fi

rm -rf "${previous}"
docker image prune -f >/dev/null
