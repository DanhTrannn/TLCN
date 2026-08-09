#!/bin/bash
set -euo pipefail

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
conf_dir="$(mktemp -d)"
cp /opt/project/spark/spark-defaults.conf "$conf_dir/spark-defaults.conf"
printf 'spark.sql.catalog.lakehouse.credential %s:%s\n' \
  "$POLARIS_SPARK_CLIENT_ID" "$POLARIS_SPARK_CLIENT_SECRET" \
  >>"$conf_dir/spark-defaults.conf"
printf 'spark.sql.catalog.lakehouse.header.Polaris-Realm %s\n' \
  "${POLARIS_REALM:-POLARIS}" >>"$conf_dir/spark-defaults.conf"
export SPARK_CONF_DIR="$conf_dir"

exec "$@"
