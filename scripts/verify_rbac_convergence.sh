#!/usr/bin/env bash
# Prove that the declarative Polaris RBAC convergence both applies a temporary
# config and prunes it again. This is self-cleaning: if anything fails after the
# probe config is applied, the EXIT trap reapplies infrastructure/polaris/rbac.yml.
set -euo pipefail

COMPOSE_PROFILES=(--profile batch)
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

tmp_config="$(mktemp --suffix=.yml)"
PROBE_APPLIED=0

restore_real_config() {
  if [[ "$PROBE_APPLIED" -eq 1 ]]; then
    printf '[warn] restoring the real Polaris RBAC configuration\n' >&2
    if compose run --rm -T --no-deps polaris-init >/dev/null 2>&1; then
      PROBE_APPLIED=0
    else
      printf '[error] could not restore infrastructure/polaris/rbac.yml; rbac_probe entities may remain\n' >&2
    fi
  fi
}

cleanup() {
  restore_real_config
  rm -f "$tmp_config"
}
trap cleanup EXIT

python3 - "$tmp_config" <<'PY'
import sys
from pathlib import Path
import yaml

source = Path("infrastructure/polaris/rbac.yml")
target = Path(sys.argv[1])
config = yaml.safe_load(source.read_text(encoding="utf-8"))
config["catalog_roles"]["spark_writer_catalog_role"]["grants"].append(
    {"type": "catalog", "privilege": "CATALOG_MANAGE_ACCESS"}
)
config["catalog_roles"]["rbac_probe_catalog_role"] = {
    "grants": [{"type": "catalog", "privilege": "CATALOG_READ_PROPERTIES"}]
}
config["principal_roles"]["rbac_probe_role"] = {
    "catalog_roles": ["rbac_probe_catalog_role"]
}
config["principals"]["rbac_probe"] = {
    "principal_roles": ["rbac_probe_role"],
    "credentials_export": {
        "client_id_var": "POLARIS_RBAC_PROBE_CLIENT_ID",
        "client_secret_var": "POLARIS_RBAC_PROBE_CLIENT_SECRET",
    },
}
target.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
PY

# Apply the temporary config. tmp_config is already an absolute path.
PROBE_APPLIED=1
expect_success "applied temporary RBAC probe configuration" \
  compose run --rm -T --no-deps \
  -v "${tmp_config}:/tmp/rbac-probe.yml:ro" \
  -e POLARIS_RBAC_CONFIG=/tmp/rbac-probe.yml \
  polaris-init

read -r -d '' PROBE_PRESENT_SCRIPT <<'SH' || true
set -eu
token="$(curl -fsS -X POST "${POLARIS_URL}/api/catalog/v1/oauth/tokens" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${POLARIS_ROOT_CLIENT_ID}" \
  --data-urlencode "client_secret=${POLARIS_ROOT_CLIENT_SECRET}" \
  --data-urlencode "scope=PRINCIPAL_ROLE:ALL" \
  | sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
if [ -z "$token" ]; then
  printf '[error] could not obtain a Polaris access token\n' >&2
  exit 1
fi
status="$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${token}" \
  -H "Polaris-Realm: ${POLARIS_REALM:-POLARIS}" \
  "${POLARIS_URL}/api/management/v1/principals/rbac_probe")"
if [ "$status" != "200" ]; then
  printf '[error] rbac_probe principal returned %s, expected 200\n' "$status" >&2
  exit 1
fi
grants="$(curl -fsS \
  -H "Authorization: Bearer ${token}" \
  -H "Polaris-Realm: ${POLARIS_REALM:-POLARIS}" \
  "${POLARIS_URL}/api/management/v1/catalogs/${POLARIS_CATALOG}/catalog-roles/spark_writer_catalog_role/grants")"
if ! printf '%s' "$grants" | grep -q 'CATALOG_MANAGE_ACCESS'; then
  printf '[error] spark_writer_catalog_role is missing the temporary CATALOG_MANAGE_ACCESS grant\n' >&2
  exit 1
fi
SH

compose run --rm -T --no-deps --entrypoint sh polaris-init -c "$PROBE_PRESENT_SCRIPT" \
  || fail "temporary RBAC probe configuration was not applied"
printf '[ok] Polaris probe principal and temporary Spark privilege are present\n'

# Reapply the real config to prove convergence prunes the probe entities.
expect_success "reapplied infrastructure/polaris/rbac.yml" \
  compose run --rm -T --no-deps polaris-init
PROBE_APPLIED=0

read -r -d '' PROBE_ABSENT_SCRIPT <<'SH' || true
set -eu
token="$(curl -fsS -X POST "${POLARIS_URL}/api/catalog/v1/oauth/tokens" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "grant_type=client_credentials" \
  --data-urlencode "client_id=${POLARIS_ROOT_CLIENT_ID}" \
  --data-urlencode "client_secret=${POLARIS_ROOT_CLIENT_SECRET}" \
  --data-urlencode "scope=PRINCIPAL_ROLE:ALL" \
  | sed -n 's/.*"access_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
if [ -z "$token" ]; then
  printf '[error] could not obtain a Polaris access token\n' >&2
  exit 1
fi
assert_missing() {
  path="$1"
  status="$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${token}" \
    -H "Polaris-Realm: ${POLARIS_REALM:-POLARIS}" \
    "${POLARIS_URL}${path}")"
  if [ "$status" != "404" ]; then
    printf '[error] %s returned %s, expected 404\n' "$path" "$status" >&2
    exit 1
  fi
}
assert_missing "/api/management/v1/principals/rbac_probe"
assert_missing "/api/management/v1/principal-roles/rbac_probe_role"
assert_missing "/api/management/v1/catalogs/${POLARIS_CATALOG}/catalog-roles/rbac_probe_catalog_role"
grants="$(curl -fsS \
  -H "Authorization: Bearer ${token}" \
  -H "Polaris-Realm: ${POLARIS_REALM:-POLARIS}" \
  "${POLARIS_URL}/api/management/v1/catalogs/${POLARIS_CATALOG}/catalog-roles/spark_writer_catalog_role/grants")"
if printf '%s' "$grants" | grep -q 'CATALOG_MANAGE_ACCESS'; then
  printf '[error] spark_writer_catalog_role still has CATALOG_MANAGE_ACCESS after convergence\n' >&2
  exit 1
fi
SH

compose run --rm -T --no-deps --entrypoint sh polaris-init -c "$PROBE_ABSENT_SCRIPT" \
  || fail "convergence did not prune the RBAC probe entities and privilege"
printf '[ok] RBAC probe principal, roles, and privilege were pruned\n'

printf 'RBAC convergence verification passed.\n'
