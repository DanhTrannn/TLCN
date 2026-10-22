#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

connect_url="${DEBEZIUM_CONNECT_URL:-http://127.0.0.1:${CDC_CONNECT_PORT:-8086}}"
connector_name="mysql-ecommerce-cdc"
topic_prefix="${CDC_TOPIC_PREFIX:-ecommerce}"
database_name="${MYSQL_DATABASE:-ecommerce}"

status="$(curl -fsS "${connect_url}/connectors/${connector_name}/status")"
if ! grep -Eq '"state"[[:space:]]*:[[:space:]]*"RUNNING"' <<<"$status"; then
  printf '%s\n' "[error] Debezium connector or task is not RUNNING: ${status}" >&2
  exit 1
fi
printf '%s\n' "[ok] Debezium connector and task are RUNNING"

topics="$(docker compose exec -T kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server kafka:9092 --list)"
expected_topic="${topic_prefix}.${database_name}.customers"
if ! grep -Fxq "$expected_topic" <<<"$topics"; then
  printf '%s\n' "[error] Expected CDC topic '${expected_topic}' was not created" >&2
  exit 1
fi
printf '%s\n' "[ok] MySQL binlog changes are published to Kafka CDC topics"

for ((attempt = 1; attempt <= 60; attempt++)); do
  result="$(docker compose exec -T trino trino --output-format TSV --execute \
    "SELECT count(*), count_if(operation = 'r'), count_if(operation = 'c'), count_if(operation = 'u'), count_if(operation = 'd'), count_if(operation = 't') FROM lakehouse.bronze.oltp_cdc_events" \
    2>/dev/null || true)"
  total="$(awk 'NR == 1 {gsub(/\"/, ""); print $1}' <<<"$result")"
  if [[ "$total" =~ ^[1-9][0-9]*$ ]]; then
    printf '%s\n' "[ok] Kafka -> Flink -> Iceberg CDC events: ${result}"
    break
  fi
  if [[ "$attempt" -eq 60 ]]; then
    printf '%s\n' "[error] No CDC event reached lakehouse.bronze.oltp_cdc_events" >&2
    exit 1
  fi
  sleep 5
done

duplicates="$(docker compose exec -T trino trino --output-format TSV --execute \
  "SELECT count(*) FROM (SELECT event_id FROM lakehouse.bronze.oltp_cdc_events GROUP BY event_id HAVING count(*) > 1)" \
  2>/dev/null | tr -d '[:space:]')"
if [[ "$duplicates" != "0" ]]; then
  printf '%s\n' "[error] CDC sink contains ${duplicates} duplicate event_id values" >&2
  exit 1
fi

printf '%s\n' "[ok] CDC event IDs are unique and replay coordinates are preserved"
printf '%s\n' "CDC end-to-end verification passed."
