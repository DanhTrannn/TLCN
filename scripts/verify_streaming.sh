#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
HEADERS_FILE="$(mktemp)"
KAFKA_OUTPUT="$(mktemp)"
trap 'rm -f "${HEADERS_FILE}" "${KAFKA_OUTPUT}"' EXIT

curl -fsS --max-time 10 -D "$HEADERS_FILE" "${API_URL}/api/v1/products" >/dev/null
REQUEST_ID="$(awk 'BEGIN {IGNORECASE=1} /^x-request-id:/ {gsub("\r", "", $2); print $2}' "$HEADERS_FILE" | tail -n 1)"
if [[ -z "$REQUEST_ID" ]]; then
  printf '%s\n' "[error] API response did not include X-Request-ID" >&2
  exit 1
fi
printf '%s\n' "[ok] Produced access event ${REQUEST_ID}"

docker compose exec -T kafka /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server kafka:9092 \
  --topic ecommerce.access_logs \
  --from-beginning \
  --timeout-ms 20000 >"$KAFKA_OUTPUT" 2>/dev/null || true

if ! grep -Fq "$REQUEST_ID" "$KAFKA_OUTPUT"; then
  printf '%s\n' "[error] Access event ${REQUEST_ID} was not found in Kafka" >&2
  exit 1
fi
printf '%s\n' "[ok] API → Kafka"

for ((i = 1; i <= 60; i++)); do
  count="$(docker compose exec -T trino trino --output-format TSV --execute \
    "SELECT COUNT(*) FROM lakehouse.gold.fact_web_events WHERE event_id = '${REQUEST_ID}'" 2>/dev/null \
    | tr -d '[:space:]' || true)"
  if [[ "$count" =~ ^[1-9][0-9]*$ ]]; then
    printf '%s\n' "[ok] Kafka → Flink → Iceberg Gold → Trino"
    printf '%s\n' "Streaming end-to-end verification passed."
    exit 0
  fi
  sleep 5
done

printf '%s\n' "[error] Event ${REQUEST_ID} did not reach lakehouse.gold.fact_web_events" >&2
exit 1
