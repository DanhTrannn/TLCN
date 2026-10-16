#!/usr/bin/env bash
set -euo pipefail

docker compose --profile batch --profile lakehouse-tools run --use-aliases --rm spark-client >/dev/null
docker compose --profile batch exec -T trino trino --output-format TSV_HEADER --execute \
  "SELECT check_name, checked_at_utc FROM lakehouse.system.stack_smoke ORDER BY checked_at_utc DESC LIMIT 1" \
  | python3 -c 'import csv,sys; rows=list(csv.DictReader(sys.stdin, delimiter="\t")); assert rows and rows[0]["check_name"] == "spark_write_through_polaris"'
printf '%s\n' "Lakehouse Spark → Iceberg/MinIO → Polaris → Trino verification passed."
