#!/usr/bin/env bash
set -euo pipefail

mysql_host="${MYSQL_HOST:-mysql}"
cdc_user="${MYSQL_CDC_USER:-debezium}"

if [[ -z "${MYSQL_ROOT_PASSWORD:-}" || -z "${MYSQL_CDC_PASSWORD:-}" ]]; then
  echo "MYSQL_ROOT_PASSWORD and MYSQL_CDC_PASSWORD are required" >&2
  exit 1
fi

# MySQL identifiers are intentionally fixed to a conservative character set.
if [[ ! "$cdc_user" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "MYSQL_CDC_USER may only contain letters, digits, and underscores" >&2
  exit 1
fi

escaped_password="${MYSQL_CDC_PASSWORD//\'/\'\'}"

mysql --protocol=tcp --host="$mysql_host" --user=root \
  --password="$MYSQL_ROOT_PASSWORD" <<SQL
CREATE USER IF NOT EXISTS '${cdc_user}'@'%' IDENTIFIED BY '${escaped_password}';
ALTER USER '${cdc_user}'@'%' IDENTIFIED BY '${escaped_password}';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT
  ON *.* TO '${cdc_user}'@'%';
FLUSH PRIVILEGES;
SQL

echo "CDC account '${cdc_user}' is ready."
