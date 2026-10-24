#!/bin/sh
set -eu

credential_file="${POLARIS_CREDENTIAL_FILE:-/run/polaris/clients.env}"
attempt=0
until [ -s "$credential_file" ]; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 120 ]; then
    echo "Polaris credential file is not ready: $credential_file" >&2
    exit 1
  fi
  sleep 1
done

# shellcheck disable=SC1090
. "$credential_file"

if [ -n "${POLARIS_TRINO_ADMIN_CLIENT_ID:-}" ]; then
  export POLARIS_CLIENT_ID="$POLARIS_TRINO_ADMIN_CLIENT_ID"
  export POLARIS_CLIENT_SECRET="$POLARIS_TRINO_ADMIN_CLIENT_SECRET"
else
  : "${POLARIS_TRINO_CLIENT_ID:?POLARIS_TRINO_CLIENT_ID is required}"
  : "${POLARIS_TRINO_CLIENT_SECRET:?POLARIS_TRINO_CLIENT_SECRET is required}"
  export POLARIS_CLIENT_ID="$POLARIS_TRINO_CLIENT_ID"
  export POLARIS_CLIENT_SECRET="$POLARIS_TRINO_CLIENT_SECRET"
fi

exec /usr/lib/trino/bin/run-trino
