#!/bin/sh
# Converge the MinIO bucket and the service identities owned by this stack.
#
# The lakehouse-* prefix is the purge boundary: this script never removes or
# modifies the root account or any principal outside that namespace.
set -eu

MINIO_ENDPOINT="${MINIO_ENDPOINT:-http://minio:9000}"
BUCKET="${MINIO_LAKEHOUSE_BUCKET:-lakehouse}"
POLICY_DIR="/bootstrap/policies"
POLICY_TMP="/tmp/lakehouse-policies"
MANAGED_USERS="lakehouse-polaris lakehouse-spark lakehouse-flink lakehouse-airflow lakehouse-trino lakehouse-trino-admin lakehouse-uploader"
MANAGED_POLICIES="lakehouse-polaris lakehouse-spark lakehouse-flink lakehouse-airflow lakehouse-trino lakehouse-trino-admin lakehouse-uploader"
IDENTITIES='lakehouse-polaris MINIO_POLARIS_ACCESS_KEY MINIO_POLARIS_SECRET_KEY
lakehouse-spark MINIO_SPARK_ACCESS_KEY MINIO_SPARK_SECRET_KEY
lakehouse-flink MINIO_FLINK_ACCESS_KEY MINIO_FLINK_SECRET_KEY
lakehouse-airflow MINIO_AIRFLOW_ACCESS_KEY MINIO_AIRFLOW_SECRET_KEY
lakehouse-trino MINIO_TRINO_ACCESS_KEY MINIO_TRINO_SECRET_KEY
lakehouse-trino-admin MINIO_TRINO_ADMIN_ACCESS_KEY MINIO_TRINO_ADMIN_SECRET_KEY
lakehouse-uploader MINIO_UPLOADER_ACCESS_KEY MINIO_UPLOADER_SECRET_KEY'

contains() {
  needle="$1"
  haystack="$2"
  for item in $haystack; do
    if [ "$item" = "$needle" ]; then
      return 0
    fi
  done
  return 1
}

# mc's table layout (column order, headers) varies between releases, so read the
# stable JSON stream and extract only the identifier. Each helper fails if the
# underlying mc command fails, which keeps set -e authoritative.
list_user_keys() {
  raw="$(mc admin user list local --json)" || return 1
  printf '%s\n' "$raw" | sed -n 's/.*"accessKey":"\([^"]*\)".*/\1/p'
}

list_policy_names() {
  raw="$(mc admin policy list local --json)" || return 1
  printf '%s\n' "$raw" | sed -n 's/.*"policy":"\([^"]*\)".*/\1/p'
}

if [ -z "${MINIO_ROOT_USER:-}" ] || [ -z "${MINIO_ROOT_PASSWORD:-}" ]; then
  echo "MINIO_ROOT_USER and MINIO_ROOT_PASSWORD must be set" >&2
  exit 1
fi

case "$MINIO_ROOT_USER" in
  lakehouse-*)
    echo "MINIO_ROOT_USER must not use the managed lakehouse-* prefix" >&2
    exit 1
    ;;
esac

# Validate every input before touching the server. Otherwise a typo in one
# credential or a missing policy file would delete the existing identities and
# only then fail, taking the stack down until it is fixed.
while read -r policy key_var secret_var; do
  key="$(printenv "$key_var" || true)"
  secret="$(printenv "$secret_var" || true)"
  if [ -z "$key" ] || [ -z "$secret" ]; then
    echo "Missing $key_var or $secret_var" >&2
    exit 1
  fi
  case "$key" in
    lakehouse-*) ;;
    *)
      echo "Access key for $policy must use the managed lakehouse-* prefix" >&2
      exit 1
      ;;
  esac
done <<EOF
$IDENTITIES
EOF

for policy in $MANAGED_POLICIES; do
  if [ ! -f "$POLICY_DIR/$policy.json" ]; then
    echo "Missing policy file: $POLICY_DIR/$policy.json" >&2
    exit 1
  fi
done

mc alias set local "$MINIO_ENDPOINT" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null

attempt=0
until mc admin info local >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "MinIO did not become ready after 60 attempts" >&2
    exit 1
  fi
  sleep 1
done

mc mb --ignore-existing "local/$BUCKET"
mc anonymous set none "local/$BUCKET"

# Remove every managed user before removing policies: deleting a user also
# detaches its policies. An unmanaged user's attachments are left intact so a
# policy still in use makes the removal below fail loudly instead of being
# force-deleted.
users="$(list_user_keys)" || {
  echo "Unable to list MinIO users" >&2
  exit 1
}
for user in $users; do
  case "$user" in
    lakehouse-*) mc admin user remove local "$user" ;;
  esac
done

policies="$(list_policy_names)" || {
  echo "Unable to list MinIO policies" >&2
  exit 1
}
for policy in $policies; do
  case "$policy" in
    lakehouse-*) mc admin policy remove local "$policy" ;;
  esac
done

mkdir -p "$POLICY_TMP"
for policy in $MANAGED_POLICIES; do
  sed "s|__MINIO_BUCKET__|${BUCKET}|g" \
    "$POLICY_DIR/$policy.json" > "$POLICY_TMP/$policy.json"
  if grep -q '__MINIO_BUCKET__' "$POLICY_TMP/$policy.json"; then
    echo "Policy placeholder was not substituted: $policy.json" >&2
    exit 1
  fi
  mc admin policy create local "$policy" "$POLICY_TMP/$policy.json"
  mc admin policy info local "$policy" >/dev/null
done

# Recreating every user makes changed secrets take effect. Each user is new, so
# it starts with no policy and receives exactly the one matching its file.
# Credentials were validated above, before anything was removed.
while read -r policy key_var secret_var; do
  key="$(printenv "$key_var")"
  secret="$(printenv "$secret_var")"
  mc admin user add local "$key" "$secret"
  mc admin policy attach local "$policy" --user "$key"
  user_json="$(mc admin user info local "$key" --json)" || {
    echo "User $key was not found after creation" >&2
    exit 1
  }
  attached_policy="$(printf '%s\n' "$user_json" | sed -n 's/.*"policyName":"\([^"]*\)".*/\1/p')"
  if [ "$attached_policy" != "$policy" ]; then
    echo "Expected exactly policy $policy on $key, found '${attached_policy}'" >&2
    exit 1
  fi
done <<EOF
$IDENTITIES
EOF

users="$(list_user_keys)" || {
  echo "Unable to list MinIO users" >&2
  exit 1
}
for user in $users; do
  case "$user" in
    lakehouse-*)
      if ! contains "$user" "$MANAGED_USERS"; then
        echo "Unexpected managed user remains: $user" >&2
        exit 1
      fi
      ;;
  esac
done

policies="$(list_policy_names)" || {
  echo "Unable to list MinIO policies" >&2
  exit 1
}
for policy in $policies; do
  case "$policy" in
    lakehouse-*)
      if ! contains "$policy" "$MANAGED_POLICIES"; then
        echo "Unexpected managed policy remains: $policy" >&2
        exit 1
      fi
      ;;
  esac
done

echo "MinIO users:"
mc admin user list local
echo "MinIO policies:"
mc admin policy list local

exit 0
