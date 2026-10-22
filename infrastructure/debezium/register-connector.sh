#!/bin/sh
set -eu

connect_url="${DEBEZIUM_CONNECT_URL:-http://debezium-connect:8083}"
connector_name="mysql-ecommerce-cdc"

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

cdc_user="$(json_escape "${MYSQL_CDC_USER:?MYSQL_CDC_USER is required}")"
cdc_password="$(json_escape "${MYSQL_CDC_PASSWORD:?MYSQL_CDC_PASSWORD is required}")"
database_name="$(json_escape "${MYSQL_DATABASE:-ecommerce}")"
topic_prefix="$(json_escape "${CDC_TOPIC_PREFIX:-ecommerce}")"

config="$(cat <<JSON
{
  "connector.class": "io.debezium.connector.mysql.MySqlConnector",
  "tasks.max": "1",
  "database.hostname": "mysql",
  "database.port": "3306",
  "database.user": "${cdc_user}",
  "database.password": "${cdc_password}",
  "database.server.id": "5401",
  "topic.prefix": "${topic_prefix}",
  "database.include.list": "${database_name}",
  "table.include.list": "${database_name}\\\\.(customers|categories|products|product_variants|carts|cart_items|wishlist_items|orders|order_items|payments|order_status_history|inventory|coupons|coupon_redemptions|refunds|product_reviews|cities|stores|store_inventory|delivery_staff|shipments|return_requests|return_items|inventory_transactions|inbound_receipts|inbound_receipt_items|shipment_attempts)",
  "snapshot.mode": "initial",
  "snapshot.locking.mode": "minimal",
  "include.schema.changes": "true",
  "provide.transaction.metadata": "true",
  "tombstones.on.delete": "true",
  "decimal.handling.mode": "string",
  "binary.handling.mode": "base64",
  "time.precision.mode": "adaptive_time_microseconds",
  "heartbeat.interval.ms": "10000",
  "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
  "schema.history.internal.kafka.topic": "schemahistory.${topic_prefix}",
  "schema.history.internal.store.only.captured.tables.ddl": "true",
  "topic.creation.enable": "true",
  "topic.creation.default.replication.factor": "1",
  "topic.creation.default.partitions": "1",
  "errors.tolerance": "none"
}
JSON
)"

echo "Registering/updating Debezium connector '${connector_name}'..."
curl --fail --silent --show-error \
  -X PUT \
  -H 'Content-Type: application/json' \
  --data "$config" \
  --output /dev/null \
  "${connect_url}/connectors/${connector_name}/config"

attempt=1
while [ "$attempt" -le 30 ]; do
  status="$(curl --fail --silent --show-error "${connect_url}/connectors/${connector_name}/status")"
  if printf '%s' "$status" | grep -Eq '"connector"[^}]*"state"[[:space:]]*:[[:space:]]*"RUNNING"' \
      && printf '%s' "$status" | grep -Eq '"tasks"[[:space:]]*:[[:space:]]*\[[^]]*"state"[[:space:]]*:[[:space:]]*"RUNNING"'; then
    echo "Debezium connector '${connector_name}' and its task are running."
    exit 0
  fi
  sleep 2
  attempt=$((attempt + 1))
done

printf '%s\n' "Connector did not become ready: ${status}" >&2
exit 1
