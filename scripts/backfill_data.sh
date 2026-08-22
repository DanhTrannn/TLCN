#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Script: backfill_data.sh
# Purpose: Generate deterministic synthetic OLTP SQL and/or Access Logs in a
#          temporary directory, import/upload to MySQL and MinIO, and automatically
#          clean up all temporary files without leaving artifacts on the host.
# ==============================================================================

CONFIG_FILE="generator/configs/small.yml"
MODE="all" # "all", "sql", "logs"
EXPECTED_REQUESTS=""

usage() {
  cat <<EOF
Usage: $0 [OPTIONS]

Options:
  -c, --config <path>           Path to generator config (default: generator/configs/small.yml)
  -m, --mode <all|oltp|logs>    Backfill target: 'oltp'/'sql' (MySQL only), 'logs' (MinIO only), or 'all' (default: all)
  -r, --expected-requests <num> Expected access log requests (optional)
  -h, --help                    Show this help message

Examples:
  $0                                        # Backfill both OLTP and Access Logs (small.yml)
  $0 --mode logs                            # Backfill only Access Logs to MinIO
  $0 --mode oltp                            # Backfill only OLTP dataset to MySQL
  $0 --config generator/configs/medium.yml  # Backfill medium dataset
EOF
  exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -c|--config)
      CONFIG_FILE="$2"
      shift 2
      ;;
    -m|--mode)
      MODE="$2"
      shift 2
      ;;
    -r|--expected-requests)
      EXPECTED_REQUESTS="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

if [[ ! -f "${CONFIG_FILE}" ]]; then
  echo "Error: Config file not found: ${CONFIG_FILE}" >&2
  exit 1
fi

# Normalize alias: sql -> oltp
if [[ "${MODE}" == "sql" ]]; then
  MODE="oltp"
fi

if [[ "${MODE}" != "all" && "${MODE}" != "oltp" && "${MODE}" != "logs" ]]; then
  echo "Error: Invalid mode '${MODE}'. Must be 'all', 'oltp' (or 'sql'), or 'logs'." >&2
  exit 1
fi

# Create a temporary directory that will be automatically removed upon script completion or error
TMP_DIR="$(mktemp -d -t tlcn-backfill-XXXXXX)"
cleanup() {
  if [[ -d "${TMP_DIR}" ]]; then
    echo "==> Cleaning up temporary files in ${TMP_DIR}..."
    rm -rf "${TMP_DIR}"
    echo "==> Cleaned up successfully. No temporary files left on host."
  fi
}
trap cleanup EXIT INT TERM

echo "========================================================================"
echo " Starting Data Backfill (Mode: ${MODE})"
echo " Config: ${CONFIG_FILE}"
echo " Temporary Workspace: ${TMP_DIR}"
echo "========================================================================"

# --- 1. OLTP Database Backfill ---
if [[ "${MODE}" == "all" || "${MODE}" == "oltp" ]]; then
  SQL_OUTPUT="${TMP_DIR}/dataset.sql"
  echo ""
  echo "--> Generating deterministic SQL dataset..."
  uv run --locked --package data-generator -- generator export-sql \
    --config "${CONFIG_FILE}" \
    --output "${SQL_OUTPUT}"

  echo "--> Importing SQL dataset into MySQL..."
  ./scripts/import_generated_sql.sh "${SQL_OUTPUT}"
fi

# --- 2. Access Logs Backfill ---
if [[ "${MODE}" == "all" || "${MODE}" == "logs" ]]; then
  LOGS_OUTPUT_DIR="${TMP_DIR}/access-logs"
  echo ""
  echo "--> Generating deterministic 30-day Access Logs..."
  LOGS_CMD=(uv run --locked --package data-generator -- generator export-logs --config "${CONFIG_FILE}" --output-directory "${LOGS_OUTPUT_DIR}")
  if [[ -n "${EXPECTED_REQUESTS}" ]]; then
    LOGS_CMD+=(--expected-requests "${EXPECTED_REQUESTS}")
  fi
  "${LOGS_CMD[@]}"

  echo "--> Uploading Access Logs to MinIO Landing Zone..."
  ./scripts/upload_generated_logs.sh "${LOGS_OUTPUT_DIR}"
fi

echo ""
echo "========================================================================"
echo " Backfill completed successfully!"
echo "========================================================================"
