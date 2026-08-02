#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 data/generator/<dataset>.sql" >&2
  exit 2
fi

sql_file="$1"
if [ ! -f "${sql_file}" ]; then
  echo "SQL file not found: ${sql_file}" >&2
  exit 2
fi

if ! head -n 1 "${sql_file}" | grep -q '^-- TLCN deterministic MySQL dataset$'; then
  echo "Refusing to import an unrecognized SQL file: ${sql_file}" >&2
  exit 2
fi

generation_run_id="$(sed -n 's/^-- generation_run_id: //p' "${sql_file}" | head -n 1)"
logical_identity="$(sed -n 's/^-- logical_identity: //p' "${sql_file}" | head -n 1)"

if [[ ! "${generation_run_id}" =~ ^[a-zA-Z0-9._-]+$ ]] || [[ ! "${logical_identity}" =~ ^[a-fA-F0-9]+$ ]]; then
  echo "Dataset metadata is missing or invalid: ${sql_file}" >&2
  exit 2
fi

product_slug_pattern="syn-${logical_identity:0:8}-%"

echo "Importing ${sql_file} into the MySQL database used by ecommerce-api..."
import_started_at=${SECONDS}
docker compose --profile core exec -T mysql-ecommerce sh -lc \
  'export MYSQL_PWD="$MYSQL_PASSWORD"; exec mysql --protocol=socket -u"$MYSQL_USER" "$MYSQL_DATABASE"' \
  < "${sql_file}"

echo "Import completed in $((SECONDS - import_started_at))s. Verifying visible catalog data..."
docker compose --profile core exec -T \
  -e IMPORT_RUN_ID="${generation_run_id}" \
  -e PRODUCT_SLUG_PATTERN="${product_slug_pattern}" \
  mysql-ecommerce sh -lc '
    export MYSQL_PWD="$MYSQL_PASSWORD"
    exec mysql --protocol=socket -u"$MYSQL_USER" "$MYSQL_DATABASE" --execute="
      SELECT
        DATABASE() AS database_name,
        (SELECT COUNT(*) FROM products WHERE slug LIKE '\''${PRODUCT_SLUG_PATTERN}'\'') AS generated_products,
        (
          SELECT COUNT(*)
          FROM product_variants AS variant
          INNER JOIN products AS product ON product.product_id = variant.product_id
          WHERE product.slug LIKE '\''${PRODUCT_SLUG_PATTERN}'\''
        ) AS generated_variants,
        (SELECT COUNT(*) FROM customers WHERE generation_run_id = '\''${IMPORT_RUN_ID}'\'') AS generated_customers,
        (SELECT COUNT(*) FROM orders WHERE generation_run_id = '\''${IMPORT_RUN_ID}'\'') AS generated_orders;
    "
  '

echo "Open http://localhost:3000/products and refresh the page."
