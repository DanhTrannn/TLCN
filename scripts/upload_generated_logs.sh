#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 data/generator/access-logs" >&2
  exit 2
fi

generated_root="$1"
landing_logs="${generated_root}/landing/logs"
if [ ! -d "${landing_logs}" ]; then
  echo "Generated Landing directory not found: ${landing_logs}" >&2
  exit 2
fi
if ! find "${landing_logs}" -type f -name '*.jsonl.gz' -print -quit | grep -q .; then
  echo "No closed .jsonl.gz files found below: ${landing_logs}" >&2
  exit 2
fi

landing_logs_absolute="$(realpath "${landing_logs}")"
echo "Uploading closed generated logs from ${landing_logs_absolute}..."
docker compose --profile batch run --rm --no-deps \
  --volume "${landing_logs_absolute}:/generated-logs:ro" \
  --entrypoint /bin/sh \
  minio-init \
  -c '
    set -eu
    mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"
    mc mirror --overwrite /generated-logs "local/$MINIO_LAKEHOUSE_BUCKET/landing/logs"
  '

echo "Upload completed under s3://${MINIO_LAKEHOUSE_BUCKET:-web-lakehouse}/landing/logs/."
