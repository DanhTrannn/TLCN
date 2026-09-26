#!/bin/sh
set -eu

# Install runtime dependencies for RBAC reconciliation engine
apk add --no-cache python3 py3-yaml jq >/dev/null

POLARIS_URL="${POLARIS_URL:-http://polaris:8181}"
REALM="${POLARIS_REALM:-POLARIS}"
CATALOG="${POLARIS_CATALOG:-lakehouse}"
CREDENTIAL_FILE="${POLARIS_CREDENTIAL_FILE:-/run/polaris/clients.env}"
POLARIS_ROOT_CLIENT_ID="${POLARIS_ROOT_CLIENT_ID:-root}"
POLARIS_ROOT_CLIENT_SECRET="${POLARIS_ROOT_CLIENT_SECRET:-password}"
CONFIG_FILE="${POLARIS_RBAC_CONFIG:-/bootstrap/rbac.yml}"

echo "Starting Polaris RBAC reconciliation from ${CONFIG_FILE}..."
exec python3 /bootstrap/sync_polaris_rbac.py \
  --config "${CONFIG_FILE}" \
  --polaris-url "${POLARIS_URL}" \
  --realm "${REALM}" \
  --root-client-id "${POLARIS_ROOT_CLIENT_ID}" \
  --root-client-secret "${POLARIS_ROOT_CLIENT_SECRET}" \
  --credential-file "${CREDENTIAL_FILE}" \
  --ready-file "/run/polaris/ready" \
  "$@"
