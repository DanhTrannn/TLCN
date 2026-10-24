#!/usr/bin/env bash
# Live negative authorization checks for the batch profile.
#
# Every check fails closed: a denial only passes when the service explicitly
# reports that the operation is not permitted, and an unexpected success fails
# the script (cleaning up anything it created first).
set -euo pipefail

COMPOSE_PROFILES=(--profile core --profile batch --profile lakehouse-tools)
compose() { docker compose "${COMPOSE_PROFILES[@]}" "$@"; }

fail() { printf '[error] %s\n' "$*" >&2; exit 1; }

expect_success() {
  local label="$1"
  shift
  if ! "$@" >/dev/null 2>&1; then fail "$label unexpectedly failed"; fi
  printf '[ok] %s\n' "$label"
}

expect_failure() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then fail "$label unexpectedly succeeded"; fi
  printf '[ok] %s denied\n' "$label"
}

# The scripts below run inside the target container. Secret values are never
# interpolated on the host: only the *names* of the variables are passed in and
# the values are read from the container's own environment or credential file.
read -r -d '' POLARIS_DENIAL_SCRIPT <<'SH' || true
set -eu
. /run/polaris/clients.env
eval "client_id=\${$POLARIS_ID_VAR}"
eval "client_secret=\${$POLARIS_SECRET_VAR}"
token="$(curl -fsS -X POST http://polaris:8181/api/catalog/v1/oauth/tokens \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${client_id}" \
  --data-urlencode "client_secret=${client_secret}" \
  --data-urlencode "scope=PRINCIPAL_ROLE:ALL" \
  | sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
if [ -z "$token" ]; then
  printf '[error] could not obtain a Polaris access token\n' >&2
  exit 1
fi
status="$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${token}" \
  -H "Polaris-Realm: ${POLARIS_REALM:-POLARIS}" \
  http://polaris:8181/api/management/v1/principals)"
if [ "$status" != "403" ]; then
  printf '[error] expected HTTP 403 from the Polaris management API, observed %s\n' "$status" >&2
  exit 1
fi
SH

assert_polaris_denied() {
  local service="$1"
  local id_var="$2"
  local secret_var="$3"
  compose exec -T \
    -e POLARIS_ID_VAR="$id_var" \
    -e POLARIS_SECRET_VAR="$secret_var" \
    "$service" sh -c "$POLARIS_DENIAL_SCRIPT" \
    || fail "Polaris management access for ${service} was not denied"
  printf '[ok] %s Polaris management denied\n' "$service"
}

assert_polaris_denied_one_shot() {
  local service="$1"
  local id_var="$2"
  local secret_var="$3"
  compose run --rm -T --no-deps --entrypoint sh \
    -e POLARIS_ID_VAR="$id_var" \
    -e POLARIS_SECRET_VAR="$secret_var" \
    "$service" -c "$POLARIS_DENIAL_SCRIPT" \
    || fail "Polaris management access for ${service} was not denied"
  printf '[ok] %s Polaris management denied\n' "$service"
}

trino_query() {
  compose exec -T trino trino --output-format TSV --execute "$1"
}

spark_sql() {
  compose run --rm -T --no-deps --use-aliases spark-client \
    /opt/spark/bin/spark-sql \
    --master spark://spark-master:7077 \
    --conf spark.driver.host=spark-client \
    --conf spark.driver.bindAddress=0.0.0.0 \
    -e "$1"
}

# Write a probe object as a named service identity. The variable names are
# passed through, and the one-shot container resolves the values from its own
# service environment.
minio_put() {
  local key_var="$1"
  local secret_var="$2"
  local object="$3"
  compose run --rm -T --no-deps \
    -e MC_KEY_VAR="$key_var" \
    -e MC_SECRET_VAR="$secret_var" \
    -e MC_OBJECT="$object" \
    --entrypoint /bin/sh minio-init -c '
      set -eu
      eval "key=\${$MC_KEY_VAR}"
      eval "secret=\${$MC_SECRET_VAR}"
      mc alias set probe http://minio:9000 "$key" "$secret" --api S3v4 >/dev/null
      printf rbac-probe | mc pipe "probe/${MINIO_LAKEHOUSE_BUCKET:-lakehouse}/$MC_OBJECT" >/dev/null
    '
}

minio_root_rm() {
  local object="$1"
  compose run --rm -T --no-deps \
    -e MC_USER_VAR=MINIO_ROOT_USER \
    -e MC_PASSWORD_VAR=MINIO_ROOT_PASSWORD \
    -e MC_OBJECT="$object" \
    --entrypoint /bin/sh minio-init -c '
      set -eu
      eval "user=\${$MC_USER_VAR}"
      eval "password=\${$MC_PASSWORD_VAR}"
      mc alias set root http://minio:9000 "$user" "$password" --api S3v4 >/dev/null
      mc rm "root/${MINIO_LAKEHOUSE_BUCKET:-lakehouse}/$MC_OBJECT" >/dev/null
    '
}

declare -A TRACKED_OBJECTS=()
track_object() { TRACKED_OBJECTS["$1"]=1; }
untrack_object() { unset 'TRACKED_OBJECTS[$1]'; }

cleanup_objects() {
  local object
  if ((${#TRACKED_OBJECTS[@]} == 0)); then
    return 0
  fi
  for object in "${!TRACKED_OBJECTS[@]}"; do
    if ! minio_root_rm "$object" >/dev/null 2>&1; then
      printf '[warn] could not remove probe object %s\n' "$object" >&2
    fi
  done
}

clean_probe_object() {
  local object="$1"
  if ! minio_root_rm "$object" >/dev/null 2>&1; then
    fail "could not remove probe object ${object}"
  fi
  untrack_object "$object"
}

ROTATION_ACTIVE=0
restore_uploader_secret() {
  if [[ "$ROTATION_ACTIVE" -eq 1 ]]; then
    printf '[warn] restoring the original MinIO uploader secret\n' >&2
    if compose run --rm -T --no-deps minio-init >/dev/null 2>&1; then
      ROTATION_ACTIVE=0
    else
      printf '[error] could not restore MINIO_UPLOADER_SECRET_KEY from .env\n' >&2
    fi
  fi
}

cleanup() {
  cleanup_objects
  restore_uploader_secret
}
trap cleanup EXIT

# 1. Reader can read.
expect_success "Trino reader can read lakehouse.system.stack_smoke" \
  trino_query "SELECT COUNT(*) FROM lakehouse.system.stack_smoke"

# 2. Reader cannot write. A unique table name ensures a stale table cannot make
#    the denial pass for the wrong reason.
probe_table="rbac_reader_probe_$(date +%s)"
if trino_query "CREATE TABLE lakehouse.system.${probe_table} (id integer)" >/dev/null 2>&1; then
  spark_sql "DROP TABLE IF EXISTS lakehouse.system.${probe_table}" >/dev/null 2>&1 \
    || printf '[warn] could not drop unexpected table lakehouse.system.%s\n' "$probe_table" >&2
  fail "Trino reader unexpectedly created lakehouse.system.${probe_table}"
fi
printf '[ok] Trino reader denied CREATE TABLE\n'

# 3. Reader cannot administer Polaris.
assert_polaris_denied trino POLARIS_TRINO_CLIENT_ID POLARIS_TRINO_CLIENT_SECRET

# 4. Spark writer can write.
writer_table="rbac_writer_probe_$(date +%s)"
if ! spark_sql "DROP TABLE IF EXISTS lakehouse.system.${writer_table}; \
CREATE TABLE lakehouse.system.${writer_table} (id integer); \
INSERT INTO lakehouse.system.${writer_table} VALUES (1)" >/dev/null 2>&1; then
  spark_sql "DROP TABLE IF EXISTS lakehouse.system.${writer_table}" >/dev/null 2>&1 || true
  fail "Spark writer could not create and write lakehouse.system.${writer_table}"
fi
if ! spark_sql "DROP TABLE IF EXISTS lakehouse.system.${writer_table}" >/dev/null 2>&1; then
  fail "Spark writer could not drop lakehouse.system.${writer_table}"
fi
printf '[ok] Spark writer wrote and cleaned up lakehouse.system.%s\n' "$writer_table"

# 5. Spark writer cannot administer Polaris.
assert_polaris_denied_one_shot spark-client POLARIS_SPARK_CLIENT_ID POLARIS_SPARK_CLIENT_SECRET

# 6. MinIO boundaries.
stamp="$(date +%s)"

spark_warehouse="warehouse/rbac-probe/spark-${stamp}"
track_object "$spark_warehouse"
expect_success "Spark PutObject warehouse/rbac-probe" \
  minio_put MINIO_SPARK_ACCESS_KEY MINIO_SPARK_SECRET_KEY "$spark_warehouse"
clean_probe_object "$spark_warehouse"

spark_landing="landing/rbac-probe/spark-${stamp}"
track_object "$spark_landing"
expect_success "Spark PutObject landing/rbac-probe" \
  minio_put MINIO_SPARK_ACCESS_KEY MINIO_SPARK_SECRET_KEY "$spark_landing"
clean_probe_object "$spark_landing"

flink_denied="landing/rbac-probe/flink-${stamp}"
track_object "$flink_denied"
expect_failure "Flink PutObject landing/rbac-probe" \
  minio_put MINIO_FLINK_ACCESS_KEY MINIO_FLINK_SECRET_KEY "$flink_denied"
untrack_object "$flink_denied"

trino_denied="warehouse/rbac-probe/trino-${stamp}"
track_object "$trino_denied"
expect_failure "Trino reader PutObject warehouse/rbac-probe" \
  minio_put MINIO_TRINO_ACCESS_KEY MINIO_TRINO_SECRET_KEY "$trino_denied"
untrack_object "$trino_denied"

airflow_denied="warehouse/rbac-probe/airflow-${stamp}"
track_object "$airflow_denied"
expect_failure "Airflow PutObject warehouse/rbac-probe" \
  minio_put MINIO_AIRFLOW_ACCESS_KEY MINIO_AIRFLOW_SECRET_KEY "$airflow_denied"
untrack_object "$airflow_denied"

airflow_state="state/rbac-probe/airflow-${stamp}"
track_object "$airflow_state"
expect_success "Airflow PutObject state/rbac-probe" \
  minio_put MINIO_AIRFLOW_ACCESS_KEY MINIO_AIRFLOW_SECRET_KEY "$airflow_state"
clean_probe_object "$airflow_state"

uploader_object="landing/logs/rbac-probe/uploader-${stamp}"
track_object "$uploader_object"
expect_success "Uploader PutObject landing/logs/rbac-probe" \
  minio_put MINIO_UPLOADER_ACCESS_KEY MINIO_UPLOADER_SECRET_KEY "$uploader_object"
clean_probe_object "$uploader_object"

# Rotation check: converge MinIO with a temporary uploader secret, prove the new
# secret works, then converge again from .env and prove the original works. The
# temporary value is passed through the environment, never through argv.
rotated_secret="rbac-probe-uploader-$(date +%s)-rotated"
ROTATION_ACTIVE=1
MINIO_UPLOADER_SECRET_KEY="$rotated_secret" \
  compose run --rm -T --no-deps minio-init >/dev/null
printf '[ok] MinIO uploader secret rotated\n'

rotated_object="landing/logs/rbac-probe/rotated-${stamp}"
track_object "$rotated_object"
MINIO_UPLOADER_SECRET_KEY="$rotated_secret" \
  expect_success "Uploader PutObject with the rotated secret" \
  minio_put MINIO_UPLOADER_ACCESS_KEY MINIO_UPLOADER_SECRET_KEY "$rotated_object"
clean_probe_object "$rotated_object"

compose run --rm -T --no-deps minio-init >/dev/null
ROTATION_ACTIVE=0
printf '[ok] MinIO uploader secret restored from .env\n'

restored_object="landing/logs/rbac-probe/restored-${stamp}"
track_object "$restored_object"
expect_success "Uploader PutObject with the restored secret" \
  minio_put MINIO_UPLOADER_ACCESS_KEY MINIO_UPLOADER_SECRET_KEY "$restored_object"
clean_probe_object "$restored_object"

# 7. Anonymous access is denied.
anonymous_status="$(curl -s -o /dev/null -w '%{http_code}' \
  "http://localhost:${MINIO_API_PORT:-9000}/${MINIO_LAKEHOUSE_BUCKET:-lakehouse}")"
if [[ "$anonymous_status" != "403" ]]; then
  fail "anonymous MinIO request returned ${anonymous_status}, expected 403"
fi
printf '[ok] Anonymous MinIO access denied (403)\n'

# 8. Convergence probe: apply a temporary config, prove it landed, then reapply
#    the real config and prove the probe entities and privilege are gone.
./scripts/verify_rbac_convergence.sh

printf 'RBAC batch verification passed.\n'
