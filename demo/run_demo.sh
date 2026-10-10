#!/usr/bin/env bash
# ==============================================================================
# Script điều khiển trình mô phỏng Tín hiệu Biến động CDC Thời Gian Thực
# D&K E-Commerce Lakehouse Platform (MIS Dashboard Demonstration)
# ==============================================================================

set -euo pipefail

CONTAINER_NAME="tlcn-ecommerce-api-1"

# Kiểm tra container đang hoạt động
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "❌ Container '${CONTAINER_NAME}' chưa được khởi chạy!"
  echo "💡 Vui lòng khởi động hệ thống bằng: docker compose --profile core up -d"
  exit 1
fi

# Chạy trình mô phỏng tương tác bên trong môi trường có sẵn database connection
if [ -t 0 ]; then
  # Terminal tương tác (TTY)
  docker exec -it -e PYTHONPATH=/app "${CONTAINER_NAME}" python /app/demo/simulate_cdc.py "$@"
else
  # Non-interactive
  docker exec -i -e PYTHONPATH=/app "${CONTAINER_NAME}" python /app/demo/simulate_cdc.py "$@"
fi
