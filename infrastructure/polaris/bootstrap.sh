#!/bin/sh
set -eu

apk add --no-cache jq >/dev/null

POLARIS_URL="${POLARIS_URL:-http://polaris:8181}"
REALM="${POLARIS_REALM:-POLARIS}"
CATALOG="${POLARIS_CATALOG:-lakehouse}"
CREDENTIAL_FILE="${POLARIS_CREDENTIAL_FILE:-/run/polaris/clients.env}"

api_call() {
  method="$1"
  url="$2"
  token="$3"
  payload="${4:-}"
  output="$(mktemp)"

  if [ -n "$payload" ]; then
    status="$(curl -sS -o "$output" -w '%{http_code}' -X "$method" "$url" \
      -H "Authorization: Bearer $token" \
      -H "Polaris-Realm: $REALM" \
      -H 'Accept: application/json' \
      -H 'Content-Type: application/json' \
      -d "$payload")"
  else
    status="$(curl -sS -o "$output" -w '%{http_code}' -X "$method" "$url" \
      -H "Authorization: Bearer $token" \
      -H "Polaris-Realm: $REALM" \
      -H 'Accept: application/json')"
  fi

  case "$status" in
    2*|409) cat "$output" ;;
    *)
      echo "Polaris API failed: $method $url returned HTTP $status" >&2
      cat "$output" >&2
      rm -f "$output"
      return 1
      ;;
  esac
  rm -f "$output"
}

obtain_token() {
  client_id="$1"
  client_secret="$2"
  curl --fail-with-body -sS -X POST "$POLARIS_URL/api/catalog/v1/oauth/tokens" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    --data-urlencode 'grant_type=client_credentials' \
    --data-urlencode "client_id=$client_id" \
    --data-urlencode "client_secret=$client_secret" \
    --data-urlencode 'scope=PRINCIPAL_ROLE:ALL' | jq -er '.access_token'
}

ensure_entity() {
  method="$1"
  url="$2"
  payload="$3"
  api_call "$method" "$url" "$ROOT_TOKEN" "$payload" >/dev/null
}

principal_has_role() {
  principal_name="$1"
  role_name="$2"
  api_call GET "$POLARIS_URL/api/management/v1/principals/$principal_name/principal-roles" "$ROOT_TOKEN" \
    | jq -e --arg role "$role_name" 'any(.roles[]?; .name == $role)' >/dev/null
}

catalog_role_has_principal_role() {
  catalog_role="$1"
  principal_role="$2"
  api_call GET "$POLARIS_URL/api/management/v1/catalogs/$CATALOG/catalog-roles/$catalog_role/principal-roles" "$ROOT_TOKEN" \
    | jq -e --arg role "$principal_role" 'any(.roles[]?; .name == $role)' >/dev/null
}

catalog_role_has_privilege() {
  catalog_role="$1"
  privilege="$2"
  api_call GET "$POLARIS_URL/api/management/v1/catalogs/$CATALOG/catalog-roles/$catalog_role/grants" "$ROOT_TOKEN" \
    | jq -e --arg privilege "$privilege" 'any(.grants[]?; .privilege == $privilege)' >/dev/null
}

load_saved_credentials() {
  [ -s "$CREDENTIAL_FILE" ] || return 1
  # shellcheck disable=SC1090
  . "$CREDENTIAL_FILE"
  [ -n "${POLARIS_SPARK_CLIENT_ID:-}" ] && \
    [ -n "${POLARIS_SPARK_CLIENT_SECRET:-}" ] && \
    [ -n "${POLARIS_TRINO_CLIENT_ID:-}" ] && \
    [ -n "${POLARIS_TRINO_CLIENT_SECRET:-}" ] && \
    obtain_token "$POLARIS_SPARK_CLIENT_ID" "$POLARIS_SPARK_CLIENT_SECRET" >/dev/null 2>&1 && \
    obtain_token "$POLARIS_TRINO_CLIENT_ID" "$POLARIS_TRINO_CLIENT_SECRET" >/dev/null 2>&1
}

principal_credentials() {
  principal_name="$1"
  response="$(api_call POST "$POLARIS_URL/api/management/v1/principals" "$ROOT_TOKEN" \
    "{\"principal\":{\"name\":\"$principal_name\",\"properties\":{\"service\":\"lakehouse\"}},\"credentialRotationRequired\":false}")"

  if ! printf '%s' "$response" | jq -e '.credentials.clientId and .credentials.clientSecret' >/dev/null 2>&1; then
    response="$(api_call POST "$POLARIS_URL/api/management/v1/principals/$principal_name/reset" "$ROOT_TOKEN" '{}')"
  fi

  printf '%s\t%s\n' \
    "$(printf '%s' "$response" | jq -er '.credentials.clientId')" \
    "$(printf '%s' "$response" | jq -er '.credentials.clientSecret')"
}

echo "Obtaining Polaris root token for realm $REALM..."
ROOT_TOKEN="$(obtain_token "$POLARIS_ROOT_CLIENT_ID" "$POLARIS_ROOT_CLIENT_SECRET")"

catalog_payload="$(jq -cn \
  --arg name "$CATALOG" \
  --arg base "$POLARIS_WAREHOUSE_LOCATION" \
  --arg allowed "$POLARIS_ALLOWED_LOCATION" \
  --arg endpoint "$POLARIS_S3_ENDPOINT" \
  --arg endpoint_internal "$POLARIS_S3_ENDPOINT_INTERNAL" \
  --arg region "$AWS_REGION" \
  '{catalog:{name:$name,type:"INTERNAL",readOnly:false,properties:{"default-base-location":$base},storageConfigInfo:{storageType:"S3",allowedLocations:[$allowed],endpoint:$endpoint,endpointInternal:$endpoint_internal,pathStyleAccess:true,region:$region}}}')"

echo "Ensuring catalog $CATALOG..."
ensure_entity POST "$POLARIS_URL/api/management/v1/catalogs" "$catalog_payload"
current_catalog="$(api_call GET "$POLARIS_URL/api/management/v1/catalogs/$CATALOG" "$ROOT_TOKEN")"
catalog_update_payload="$(printf '%s' "$current_catalog" | jq -c \
  --arg base "$POLARIS_WAREHOUSE_LOCATION" \
  --arg allowed "$POLARIS_ALLOWED_LOCATION" \
  --arg endpoint "$POLARIS_S3_ENDPOINT" \
  --arg endpoint_internal "$POLARIS_S3_ENDPOINT_INTERNAL" \
  --arg region "$AWS_REGION" \
  '{currentEntityVersion:.entityVersion,properties:{"default-base-location":$base},storageConfigInfo:{storageType:"S3",allowedLocations:[$allowed],endpoint:$endpoint,endpointInternal:$endpoint_internal,pathStyleAccess:true,region:$region}}')"
api_call PUT "$POLARIS_URL/api/management/v1/catalogs/$CATALOG" "$ROOT_TOKEN" "$catalog_update_payload" >/dev/null

ensure_entity POST "$POLARIS_URL/api/management/v1/principal-roles" \
  '{"principalRole":{"name":"spark_writer_role","properties":{}}}'
ensure_entity POST "$POLARIS_URL/api/management/v1/principal-roles" \
  '{"principalRole":{"name":"trino_reader_role","properties":{}}}'
ensure_entity POST "$POLARIS_URL/api/management/v1/catalogs/$CATALOG/catalog-roles" \
  '{"catalogRole":{"name":"spark_writer_catalog_role","properties":{}}}'
ensure_entity POST "$POLARIS_URL/api/management/v1/catalogs/$CATALOG/catalog-roles" \
  '{"catalogRole":{"name":"trino_reader_catalog_role","properties":{}}}'

if load_saved_credentials; then
  echo "Reusing valid Spark and Trino credentials from persistent volume."
else
  echo "Creating or rotating service-principal credentials..."
  spark_credentials="$(principal_credentials spark_writer)"
  trino_credentials="$(principal_credentials trino_reader)"
  POLARIS_SPARK_CLIENT_ID="$(printf '%s' "$spark_credentials" | cut -f1)"
  POLARIS_SPARK_CLIENT_SECRET="$(printf '%s' "$spark_credentials" | cut -f2)"
  POLARIS_TRINO_CLIENT_ID="$(printf '%s' "$trino_credentials" | cut -f1)"
  POLARIS_TRINO_CLIENT_SECRET="$(printf '%s' "$trino_credentials" | cut -f2)"

  umask 077
  cat >"$CREDENTIAL_FILE" <<EOF
POLARIS_SPARK_CLIENT_ID='$POLARIS_SPARK_CLIENT_ID'
POLARIS_SPARK_CLIENT_SECRET='$POLARIS_SPARK_CLIENT_SECRET'
POLARIS_TRINO_CLIENT_ID='$POLARIS_TRINO_CLIENT_ID'
POLARIS_TRINO_CLIENT_SECRET='$POLARIS_TRINO_CLIENT_SECRET'
EOF
fi

if ! principal_has_role spark_writer spark_writer_role; then
  ensure_entity PUT "$POLARIS_URL/api/management/v1/principals/spark_writer/principal-roles" \
    '{"principalRole":{"name":"spark_writer_role"}}'
fi
if ! principal_has_role trino_reader trino_reader_role; then
  ensure_entity PUT "$POLARIS_URL/api/management/v1/principals/trino_reader/principal-roles" \
    '{"principalRole":{"name":"trino_reader_role"}}'
fi
if ! catalog_role_has_principal_role spark_writer_catalog_role spark_writer_role; then
  ensure_entity PUT "$POLARIS_URL/api/management/v1/principal-roles/spark_writer_role/catalog-roles/$CATALOG" \
    '{"catalogRole":{"name":"spark_writer_catalog_role"}}'
fi
if ! catalog_role_has_principal_role trino_reader_catalog_role trino_reader_role; then
  ensure_entity PUT "$POLARIS_URL/api/management/v1/principal-roles/trino_reader_role/catalog-roles/$CATALOG" \
    '{"catalogRole":{"name":"trino_reader_catalog_role"}}'
fi

if ! catalog_role_has_privilege spark_writer_catalog_role CATALOG_MANAGE_CONTENT; then
  ensure_entity PUT "$POLARIS_URL/api/management/v1/catalogs/$CATALOG/catalog-roles/spark_writer_catalog_role/grants" \
    '{"type":"catalog","privilege":"CATALOG_MANAGE_CONTENT"}'
fi
for privilege in TABLE_READ_DATA TABLE_FULL_METADATA VIEW_FULL_METADATA NAMESPACE_FULL_METADATA CATALOG_READ_PROPERTIES; do
  if ! catalog_role_has_privilege trino_reader_catalog_role "$privilege"; then
    ensure_entity PUT "$POLARIS_URL/api/management/v1/catalogs/$CATALOG/catalog-roles/trino_reader_catalog_role/grants" \
      "{\"type\":\"catalog\",\"privilege\":\"$privilege\"}"
  fi
done

SPARK_TOKEN="$(obtain_token "$POLARIS_SPARK_CLIENT_ID" "$POLARIS_SPARK_CLIENT_SECRET")"
for namespace in bronze silver gold quarantine system; do
  api_call POST "$POLARIS_URL/api/catalog/v1/$CATALOG/namespaces" "$SPARK_TOKEN" \
    "{\"namespace\":[\"$namespace\"],\"properties\":{}}" >/dev/null
done

chmod 0444 "$CREDENTIAL_FILE"
touch /run/polaris/ready
echo "Polaris catalog, namespaces and least-privilege service principals are ready."
