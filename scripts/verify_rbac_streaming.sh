#!/usr/bin/env bash
# Live negative authorization checks for the streaming profile.
#
# The positive Flink write path is covered by scripts/verify_streaming.sh; run
# that script first, then this one, so the isolation checks below are meaningful.
set -euo pipefail

COMPOSE_PROFILES=(--profile core --profile streaming)
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

trap cleanup_objects EXIT

# 1. Flink carries only its own Polaris principal.
compose exec -T flink-jobmanager sh -c \
  'test -z "${POLARIS_SPARK_CLIENT_ID:-}" && test -n "${POLARIS_FLINK_CLIENT_ID:-}"' \
  || fail "Flink jobmanager does not isolate the Flink Polaris principal"
printf '[ok] Flink has only its own Polaris principal\n'

# 2. Flink cannot administer Polaris.
assert_polaris_denied flink-jobmanager POLARIS_FLINK_CLIENT_ID POLARIS_FLINK_CLIENT_SECRET

stamp="$(date +%s)"

# 3. Flink MinIO user cannot write Spark's landing prefix.
flink_denied="landing/rbac-probe/flink-${stamp}"
track_object "$flink_denied"
expect_failure "Flink PutObject landing/rbac-probe" \
  minio_put MINIO_FLINK_ACCESS_KEY MINIO_FLINK_SECRET_KEY "$flink_denied"
untrack_object "$flink_denied"

# 4. Flink MinIO user can write its own warehouse prefix.
flink_allowed="warehouse/rbac-probe/flink-${stamp}"
track_object "$flink_allowed"
expect_success "Flink PutObject warehouse/rbac-probe" \
  minio_put MINIO_FLINK_ACCESS_KEY MINIO_FLINK_SECRET_KEY "$flink_allowed"
clean_probe_object "$flink_allowed"

# 5. The default Trino service has no admin Polaris credential.
compose exec -T trino sh -c 'test -z "${POLARIS_TRINO_ADMIN_CLIENT_ID:-}"' \
  || fail "Default Trino exposes POLARIS_TRINO_ADMIN_CLIENT_ID"
printf '[ok] Default Trino has no admin Polaris credential\n'

# 6. The default Trino service has no admin MinIO key.
compose exec -T trino sh -c \
  'test -z "${MINIO_TRINO_ADMIN_ACCESS_KEY:-}" && test -n "${MINIO_TRINO_ACCESS_KEY:-}"' \
  || fail "Default Trino exposes an admin MinIO key or lacks its reader key"
printf '[ok] Default Trino has no admin MinIO key\n'

# 7. The positive Flink path is covered by the preceding streaming smoke test.
printf '[ok] Positive Flink path is covered by scripts/verify_streaming.sh (run it first)\n'

printf 'RBAC streaming verification passed.\n'
