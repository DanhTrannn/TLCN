#!/usr/bin/env bash
set -euo pipefail

docker compose --profile batch --profile lakehouse-tools run --use-aliases --rm spark-client
docker compose --profile batch --profile bi exec -T trino \
  trino --execute "SELECT check_name, checked_at_utc FROM lakehouse.system.stack_smoke ORDER BY checked_at_utc DESC LIMIT 5"
