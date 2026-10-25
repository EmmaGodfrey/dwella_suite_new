#!/bin/sh
set -eu

# Restrict CSP additions to one exact HTTPS origin, never wildcard schemes.
if [ -n "${MEDIA_CSP_ORIGIN:-}" ] && ! printf '%s' "$MEDIA_CSP_ORIGIN" | grep -Eq '^https://[a-zA-Z0-9.-]+(:[0-9]+)?$'; then
  echo 'MEDIA_CSP_ORIGIN must be one HTTPS origin without a path.' >&2
  exit 1
fi
