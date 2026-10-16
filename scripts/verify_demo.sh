#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

printf '%s\n' "Verifying core application..."
./scripts/verify_core.sh

printf '%s\n' "Verifying Iceberg catalog and query path..."
./scripts/lakehouse_smoke.sh

if [[ "${VERIFY_BATCH_PIPELINE:-1}" == "1" ]]; then
  printf '%s\n' "Verifying scheduled OLTP batch path..."
  ./scripts/verify_batch_pipeline.sh
fi

if [[ "${VERIFY_STREAMING_PIPELINE:-1}" == "1" ]]; then
  printf '%s\n' "Verifying access-log streaming path..."
  ./scripts/verify_streaming.sh
fi

printf '%s\n' "All requested demo paths passed."
