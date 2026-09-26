#!/bin/bash
set -euo pipefail

sql_file="$1"
credential_file="${POLARIS_CREDENTIAL_FILE:-/run/polaris/clients.env}"
for _ in $(seq 1 120); do
  if [[ -s "$credential_file" ]]; then
    break
  fi
  sleep 1
done

if [[ ! -s "$credential_file" ]]; then
  echo "Polaris credential file is not ready: $credential_file" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$credential_file"

export POLARIS_FLINK_CLIENT_ID="${POLARIS_FLINK_CLIENT_ID:-${POLARIS_SPARK_CLIENT_ID:-}}"
export POLARIS_FLINK_CLIENT_SECRET="${POLARIS_FLINK_CLIENT_SECRET:-${POLARIS_SPARK_CLIENT_SECRET:-}}"
export POLARIS_REALM="${POLARIS_REALM:-POLARIS}"

tmp_sql="$(mktemp)"
envsubst < "$sql_file" > "$tmp_sql"

/opt/flink/bin/sql-client.sh -f "$tmp_sql"
rm -f "$tmp_sql"
