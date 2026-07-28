#!/usr/bin/env bash
set -euo pipefail

compose=(docker compose)
database_service="${MYSQL_ECOMMERCE_SERVICE:-mysql-ecommerce}"

"${compose[@]}" --profile core exec -T "${database_service}" sh -s <<'CONTAINER_SCRIPT'
set -eu

export MYSQL_PWD="${MYSQL_ROOT_PASSWORD}"

attempt=0
while :; do
  required_table_count="$(
    mysql --protocol=socket -uroot --batch --skip-column-names \
      -e "SELECT COUNT(*) FROM information_schema.tables
          WHERE table_schema = '${MYSQL_DATABASE}'
            AND table_name IN (
              'customers', 'categories', 'products', 'product_variants',
              'inventory', 'carts', 'cart_items', 'wishlist_items',
              'orders', 'order_items', 'payments', 'order_status_history'
            );" 2>/dev/null || true
  )"

  if [ "${required_table_count:-0}" -eq 12 ]; then
    break
  fi

  attempt=$((attempt + 1))
  if [ "${attempt}" -ge 60 ]; then
    echo "Timed out waiting for the 12 OLTP source tables." >&2
    exit 1
  fi
  sleep 2
done

mysql --protocol=socket -uroot <<SQL
REVOKE ALL PRIVILEGES, GRANT OPTION
  FROM '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`customers\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`categories\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`products\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`product_variants\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`inventory\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`carts\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`cart_items\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`wishlist_items\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`orders\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`order_items\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`payments\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
GRANT SELECT ON \`${MYSQL_DATABASE}\`.\`order_status_history\`
  TO '${MYSQL_ECOMMERCE_READER_USER}'@'%';
FLUSH PRIVILEGES;
SQL

allowed_count="$(
  mysql --protocol=socket -uroot --batch --skip-column-names \
    -e "SELECT COUNT(*) FROM information_schema.table_privileges
        WHERE table_schema = '${MYSQL_DATABASE}'
          AND grantee = CONCAT(QUOTE('${MYSQL_ECOMMERCE_READER_USER}'), '@', QUOTE('%'))
          AND privilege_type = 'SELECT';"
)"

if [ "${allowed_count}" -ne 12 ]; then
  echo "Expected 12 table-level SELECT grants, found ${allowed_count}." >&2
  exit 1
fi

credential_grant_count="$(
  mysql --protocol=socket -uroot --batch --skip-column-names \
    -e "SELECT COUNT(*) FROM information_schema.table_privileges
        WHERE table_schema = '${MYSQL_DATABASE}'
          AND table_name = 'customer_credentials'
          AND grantee = CONCAT(QUOTE('${MYSQL_ECOMMERCE_READER_USER}'), '@', QUOTE('%'));"
)"

if [ "${credential_grant_count}" -ne 0 ]; then
  echo "The DE reader must not have access to customer_credentials." >&2
  exit 1
fi

echo "Granted read-only access to 12 OLTP source tables."
CONTAINER_SCRIPT
