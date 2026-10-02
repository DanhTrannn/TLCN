#!/usr/bin/env bash
# ==============================================================================
# Script: stop_all.sh
# Purpose: Gracefully stop all platform services across all profiles.
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

echo "Stopping all D&K E-Commerce Lakehouse platform containers..."
docker compose --profile core --profile batch --profile streaming down "$@"
echo "All services stopped."
