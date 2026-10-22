#!/usr/bin/env bash
set -euo pipefail

DAG_ID="lakehouse_oltp_pipeline"
RUN_ID="manual__verify_$(date -u +%Y%m%dT%H%M%SZ)"
MAX_POLLS="${BATCH_VERIFY_MAX_POLLS:-240}"

docker compose exec -T ecommerce-api python -m database.seeds.seed_demo_scenarios >/dev/null
printf '%s\n' "[ok] Demo source data is present in MySQL"

docker compose exec -T airflow-webserver airflow dags unpause "$DAG_ID" >/dev/null
docker compose exec -T airflow-webserver airflow dags trigger "$DAG_ID" --run-id "$RUN_ID" >/dev/null
printf '%s\n' "[run] ${DAG_ID} ${RUN_ID}"

for ((i = 1; i <= MAX_POLLS; i++)); do
  state="$(
    docker compose exec -T airflow-webserver airflow dags list-runs \
      --dag-id "$DAG_ID" --output json --no-backfill 2>/dev/null \
      | python3 -c '
import json
import sys

target = sys.argv[1]
runs = json.load(sys.stdin)
print(next((run["state"] for run in runs if run["run_id"] == target), "missing"))
' "$RUN_ID"
  )"
  case "$state" in
    success)
      printf '%s\n' "[ok] Batch DAG completed"
      break
      ;;
    failed)
      printf '%s\n' "[error] Batch DAG failed: ${RUN_ID}" >&2
      exit 1
      ;;
  esac
  if [[ "$i" -eq "$MAX_POLLS" ]]; then
    printf '%s\n' "[error] Batch DAG timed out in state '${state}'" >&2
    exit 1
  fi
  sleep 5
done

docker compose exec -T trino trino --output-format TSV_HEADER --execute \
  "SELECT COUNT(*) AS order_rows FROM lakehouse.gold.fact_order" \
  | python3 -c 'import csv,sys; rows=list(csv.DictReader(sys.stdin, delimiter="\t")); assert rows and int(rows[0]["order_rows"]) > 0'

docker compose exec -T trino trino --output-format TSV_HEADER --execute \
  "SELECT COUNT(*) AS mart_rows FROM lakehouse.gold.mart_sales_daily" \
  | python3 -c 'import csv,sys; rows=list(csv.DictReader(sys.stdin, delimiter="\t")); assert rows and int(rows[0]["mart_rows"]) > 0'

docker compose exec -T trino trino --output-format TSV_HEADER --execute \
  "WITH latest AS (
     SELECT phase, MAX(checked_at) AS checked_at
     FROM lakehouse.system.data_quality_results
     GROUP BY phase
   )
   SELECT q.phase, COUNT(*) AS checks, count_if(q.status = 'FAILED') AS failed
   FROM lakehouse.system.data_quality_results q
   JOIN latest l ON q.phase = l.phase AND q.checked_at = l.checked_at
   GROUP BY q.phase
   ORDER BY q.phase" \
  | python3 -c '
import csv
import sys

rows = {row["phase"]: row for row in csv.DictReader(sys.stdin, delimiter="\t")}
expected = {"pre_gold_reconciliation", "post_gold"}
assert expected.issubset(rows), rows
assert all(int(rows[phase]["checks"]) > 0 for phase in expected), rows
assert all(int(rows[phase]["failed"]) == 0 for phase in expected), rows
'

printf '%s\n' "Batch MySQL → Landing → Bronze → Silver → Gold verification passed."
