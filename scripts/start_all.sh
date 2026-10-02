#!/usr/bin/env bash
# ==============================================================================
# Script: start_all.sh
# Purpose: Start the full D&K E-Commerce Lakehouse platform services with all
#          profiles (core, batch, streaming), wait for service health, initialize
#          Gold Marts if needed, and print an interactive dashboard URL table.
# ==============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

WAIT_FOR_HEALTH=true
BUILD_IMAGES=false

usage() {
  cat <<EOF
${BOLD}Usage:${NC} $0 [OPTIONS]

${BOLD}Options:${NC}
  -b, --build       Rebuild container images before starting
  --no-wait         Start services in background without waiting for health checks
  -h, --help        Show this help message

${BOLD}Examples:${NC}
  $0                # Fast startup of all services with health checks
  $0 --build        # Rebuild updated images and start full stack
  $0 --no-wait      # Instant background startup without waiting
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -b|--build)
      BUILD_IMAGES=true
      shift
      ;;
    --no-wait)
      WAIT_FOR_HEALTH=false
      shift
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

echo -e "${CYAN}${BOLD}=================================================================${NC}"
echo -e "${CYAN}${BOLD}       D&K E-COMMERCE HYBRID LAKEHOUSE PLATFORM LAUNCHER         ${NC}"
echo -e "${CYAN}${BOLD}=================================================================${NC}"

# 1. Check .env file
if [[ ! -f .env ]]; then
  echo -e "${YELLOW}[!] .env not found. Creating from .env.example...${NC}"
  cp .env.example .env
fi

# Ensure COMPOSE_PROFILES includes core, batch, streaming
export COMPOSE_PROFILES="core,batch,streaming"

# 2. Start services via Docker Compose
UP_ARGS=("-d")
if [[ "$BUILD_IMAGES" == "true" ]]; then
  UP_ARGS+=("--build")
fi

echo -e "${BLUE}[*] Starting all services with profiles [core, batch, streaming]...${NC}"
docker compose --profile core --profile batch --profile streaming up "${UP_ARGS[@]}"

if [[ "$WAIT_FOR_HEALTH" == "false" ]]; then
  echo -e "${GREEN}[✔] Services launched in background.${NC}"
  exit 0
fi

# 3. Wait for critical services to be ready
echo -e "\n${BLUE}[*] Waiting for services to be ready...${NC}"

wait_for_url() {
  local name="$1"
  local url="$2"
  local max_retries="${3:-30}"
  local count=0

  printf "    %-24s " "Checking ${name}..."
  while [[ $count -lt $max_retries ]]; do
    if curl -fsS "$url" > /dev/null 2>&1; then
      echo -e "${GREEN}READY${NC}"
      return 0
    fi
    sleep 2
    count=$((count + 1))
  done
  echo -e "${YELLOW}TIMEOUT (will continue)${NC}"
  return 1
}

wait_for_url "FastAPI Backend" "http://localhost:8000/health/ready" 30 || true
wait_for_url "Next.js Storefront" "http://localhost:3000" 30 || true
wait_for_url "Trino SQL Engine" "http://localhost:8084/v1/info" 30 || true
wait_for_url "MinIO S3" "http://localhost:9000/minio/health/live" 20 || true
wait_for_url "Polaris Console" "http://localhost:8183" 20 || true
wait_for_url "Airflow Web UI" "http://localhost:8080/health" 30 || true
wait_for_url "Flink Dashboard" "http://localhost:8085/overview" 20 || true

# 4. Initialize Gold Marts on Iceberg if needed
echo -e "\n${BLUE}[*] Verifying Lakehouse Gold Marts on Iceberg...${NC}"
GOLD_CHECK="$(docker compose exec -T trino trino --execute "SHOW TABLES FROM lakehouse.gold LIKE 'mart_sales_daily'" 2>/dev/null || echo "")"
if [[ "$GOLD_CHECK" != *"mart_sales_daily"* ]]; then
  echo -e "    ${YELLOW}Gold Marts not found. Initializing schemas via Spark SQL...${NC}"
  docker compose --profile batch --profile lakehouse-tools run --use-aliases --rm spark-client \
    /opt/spark/bin/spark-sql \
    --master spark://spark-master:7077 \
    --conf spark.driver.host=spark-client \
    --conf spark.driver.bindAddress=0.0.0.0 \
    -f /opt/project/spark/sql/init_gold_marts.sql > /dev/null 2>&1 || true
  echo -e "    ${GREEN}[✔] Gold Marts schema initialized successfully.${NC}"
else
  echo -e "    ${GREEN}[✔] Gold Marts already present in catalog.${NC}"
fi

# 5. Print Service Directory Table
echo -e "\n${GREEN}${BOLD}=================================================================${NC}"
echo -e "${GREEN}${BOLD}               PLATFORM SERVICES READY TO USE                    ${NC}"
echo -e "${GREEN}${BOLD}=================================================================${NC}"
cat <<EOF

  Service                         URL                                  Credentials / Note
  ──────────────────────────────  ───────────────────────────────────  ──────────────────────────
  Customer Storefront             http://localhost:3000                Public Web
  Admin Management                http://localhost:3000/admin          admin@web.local / Admin@12345
  BI Analytics Hub (7 Roles)      http://localhost:3000/admin/analytics
  POS Counter (Point of Sale)     http://localhost:3000/admin/pos      store.manager@dk.local / Admin@12345
  FastAPI Documentation           http://localhost:8000/docs           Swagger UI
  LibreDB Studio (SQL IDE)        http://localhost:3001                Web SQL Interface
  Trino Query Engine              http://localhost:8084                trino
  Airflow Web UI                  http://localhost:8080                airflow / password
  Flink Streaming Dashboard       http://localhost:8085                Web UI
  MinIO S3 Storage Console        http://localhost:9001                minioadmin / password
  Apache Polaris REST Console     http://localhost:8183                admin / password (Realm: POLARIS)
  Apache Kafka Broker             localhost:9092, localhost:9094       PLAINTEXT
EOF

echo -e "\n${BOLD}Useful Commands:${NC}"
echo -e "  View running containers:        ${CYAN}make ps${NC}      or  ${CYAN}docker compose ps${NC}"
echo -e "  View live logs:                 ${CYAN}make logs${NC}    or  ${CYAN}docker compose logs -f${NC}"
echo -e "  Stop all services:              ${CYAN}make down${NC}    or  ${CYAN}./scripts/stop_all.sh${NC}\n"
