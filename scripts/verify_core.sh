#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
STOREFRONT_URL="${STOREFRONT_URL:-http://localhost:3000}"
ADMIN_EMAIL="${API_BOOTSTRAP_ADMIN_EMAIL:-admin@web.local}"
ADMIN_PASSWORD="${API_BOOTSTRAP_ADMIN_PASSWORD:-Admin@12345}"
COOKIE_JAR="$(mktemp)"
trap 'rm -f "${COOKIE_JAR}"' EXIT

wait_for_url() {
  local name="$1"
  local url="$2"
  local attempts="${3:-60}"
  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS --max-time 5 "$url" >/dev/null; then
      printf '%s\n' "[ok] ${name}: ${url}"
      return 0
    fi
    sleep 2
  done
  printf '%s\n' "[error] ${name} did not become ready: ${url}" >&2
  return 1
}

wait_for_url "FastAPI readiness" "${API_URL}/health/ready"
wait_for_url "Next.js storefront" "${STOREFRONT_URL}"

curl -fsS --max-time 10 "${API_URL}/openapi.json" \
  | python3 -c 'import json,sys; doc=json.load(sys.stdin); assert "/api/v1/admin/analytics/role-metrics" in doc["paths"]'
printf '%s\n' "[ok] OpenAPI exposes the analytics contract"

curl -fsS --max-time 10 \
  -c "$COOKIE_JAR" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}" \
  "${API_URL}/api/v1/auth/login" \
  | python3 -c 'import json,sys; body=json.load(sys.stdin); assert body["role"] == "admin"'
printf '%s\n' "[ok] Admin login contract"

curl -fsS --max-time 10 -b "$COOKIE_JAR" "${API_URL}/api/v1/auth/me" \
  | python3 -c 'import json,sys; body=json.load(sys.stdin); assert body["role"] == "admin"'
printf '%s\n' "[ok] Authenticated session contract"

curl -fsS --max-time 15 -b "$COOKIE_JAR" \
  "${API_URL}/api/v1/admin/analytics/role-metrics?target_role=executive" \
  | python3 -c 'import json,sys; body=json.load(sys.stdin); assert body["role"] == "executive"; assert body["data_source"] in {"lakehouse", "oltp_fallback"}; assert isinstance(body["is_degraded"], bool)'
printf '%s\n' "[ok] Analytics serves Lakehouse data or an explicit OLTP degraded response"

printf '%s\n' "Core application verification passed."
