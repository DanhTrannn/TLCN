# Project Structure and Architecture

This document describes the repository structure, component architecture, and dependency rules for the D&K E-Commerce Data Platform. The project is organized as a monorepo containing the operational e-commerce application, lakehouse infrastructure, batch ingestion pipelines, and deterministic data generation tooling.

## 1. System Architecture

The following diagram illustrates the data flow and system boundaries:

```mermaid
flowchart LR
    Browser[Storefront Next.js] --> API[Ecommerce API FastAPI]
    Generator[Data Generator CLI] --> API
    API --> OLTP[(MySQL 8.4 OLTP)]
    Browser --> Logs[Structured JSON Access Logs]
    API --> Logs

    OLTP -->|Batch Extract (16 tables)| Landing[(MinIO Landing Zone)]
    Logs -->|15-minute JSONL.gz| Landing
    Landing --> Bronze[Bronze Iceberg]
    Bronze --> Silver[Silver Iceberg]
    Silver --> Gold[Gold Iceberg]
    Silver --> Quarantine[Quarantine]

    Airflow[Airflow Orchestrator] --> Landing
    Airflow --> Bronze
    Airflow --> Silver
    Airflow --> Gold
    Airflow --> Maintenance[Iceberg Maintenance]

    Spark[Spark Writer Engine] --> Bronze
    Spark --> Silver
    Spark --> Gold
    Spark --> Maintenance

    Polaris[Polaris REST Catalog] --- Bronze
    Polaris --- Silver
    Polaris --- Gold
    Trino[Trino Query Engine] --> Polaris
    Trino --> Gold
    Superset[Superset BI] --> Trino
    Gold --> Features[Repurchase Features & Labels]
    Features --> Model[Train & Score ML]
```

### 1.1. Dependency Rules

1. **Presentation Boundary:** The Storefront communicates exclusively with the Ecommerce API via HTTP/JSON.
2. **Short Transactions:** The Ecommerce API writes to the MySQL OLTP database via short transactions and emits structured JSON access logs to stdout.
3. **Read-Only Ingestion:** The Data Engineering (DE) extractor uses a read-only account scoped strictly to the 16 allowed analytical tables.
4. **Single Writer Principal:** Apache Airflow orchestrates workflows; Apache Spark executes the batch ingestion, transformations, and Iceberg commits. Spark is the sole Iceberg writer.
5. **Catalog Decoupling:** Apache Polaris manages table metadata, namespaces, and RBAC privileges. It does not perform compute or store data files.
6. **Read-Only Query Engine:** Trino is the distributed SQL engine reading Iceberg tables via Polaris. Apache Superset connects only to Trino.
7. **Isolation of Operational DB:** Analytical dashboards, feature engineering, and ML pipelines never read directly from the primary OLTP database.

---

## 2. Directory Layout

```text
.
├── apps/
│   └── storefront/                       # Next.js 15 customer storefront and admin UI
├── services/
│   └── ecommerce-api/                    # FastAPI backend with structured access logging
├── database/
│   ├── alembic.ini                       # Alembic migration configuration
│   ├── migrations/                       # Alembic schema versions (0001 to 0009)
│   └── seeds/                            # Master catalog seed scripts
├── generator/
│   ├── configs/                          # Dataset scale scenarios (small, medium, large)
│   ├── src/generator/                    # Deterministic data generator CLI package (v0.6.0)
│   └── tests/                            # Generator distribution & SQL tests (54 tests)
├── pipelines/
│   ├── config/                           # Lakehouse table configurations (default.yml)
│   ├── src/lakehouse/                    # Core library (config, cursor, landing, spark, validate)
│   ├── src/jobs/                         # Spark batch jobs (extract_oltp.py, jdbc_probe.py)
│   └── tests/                            # Pipeline & cursor tests (32 tests)
├── airflow/
│   ├── dags/                             # Airflow DAGs (ingest_oltp_batch.py)
│   └── logs/                             # Airflow operational logs
├── infrastructure/
│   ├── docker/                           # Custom images (Airflow, Superset)
│   ├── fluent-bit/                       # Real-time access log collector config
│   ├── polaris/                          # Idempotent Polaris catalog bootstrap script
│   ├── postgres/                         # Multi-database init scripts (polaris, airflow, superset)
│   ├── spark/                            # Spark Dockerfile, credentials script & conf
│   ├── trino/                            # Trino Iceberg REST catalog configuration
│   └── superset/                         # Superset datasources and configuration
├── docs/                                 # Architecture specs, data contracts, and runbooks
│   ├── architecture/                     # Project structure, OLTP schema, access log designs
│   ├── contracts/                        # JSON schema contracts
│   ├── design-system/                    # UI design tokens and component guidelines
│   ├── pipelines/                        # Batch pipeline implementation guides
│   ├── project/                          # Scope, Lakehouse design plan, Web design plan
│   └── runbook/                          # Setup, startup flow, and operational runbooks
├── scripts/                              # Utility shell scripts and traffic simulator
├── tests/                                # Monorepo cross-component testing guides
├── docker-compose.yml                    # Multi-profile Docker compose stack
├── pyproject.toml                        # Workspace root pyproject configuration
└── uv.lock                               # Pinned dependencies lockfile
```

---

## 3. Python Workspace Configuration

The monorepo uses [`uv`](https://docs.astral.sh/uv/) as the package manager and workspace orchestrator. The workspace consists of three packages sharing a single `uv.lock` file:

- **`ecommerce-api`** (`services/ecommerce-api`): FastAPI, SQLAlchemy 2.0, Alembic, PyMySQL, Argon2, PyJWT.
- **`data-generator`** (`generator`): Faker, PyYAML, Argon2, HTTPX.
- **`batch-pipeline`** (`pipelines`): PyYAML, PyMySQL, Boto3, PyArrow.

Infrastructure components (Trino, Polaris, MinIO, Superset, Spark) are pinned via standard container images or custom Dockerfiles and do not interact with the Python host workspace.

---

## 4. Docker Runtime Profiles

The platform uses Docker Compose profiles to isolate service lifecycle:

| Profile | Services | Purpose |
|---|---|---|
| `core` | `mysql`, `ecommerce-api`, `storefront` | Operational e-commerce web application and primary database |
| `batch` | `minio`, `minio-init`, `fluent-bit`, `postgres`, `polaris-bootstrap`, `polaris`, `polaris-init`, `polaris-console`, `spark-master`, `spark-worker`, `airflow-init`, `airflow-webserver`, `airflow-scheduler` | Log collection, object landing, Iceberg ETL, catalog RBAC, and Airflow orchestration |
| `bi` | `postgres`, `trino`, `superset-init`, `superset` | Distributed SQL query engine and Superset BI dashboards |
| `lakehouse-tools` | `spark-client` | Ad-hoc Spark CLI verification and SQL smoke tests |

### Service Port Allocations

| Service | Port | Protocol | Description |
|---|---|---|---|
| **Storefront** | `3000` | HTTP | Customer web store & operator console |
| **MySQL** | `3306` | TCP | OLTP relational database |
| **Ecommerce API** | `8000` | HTTP | FastAPI REST endpoints & Swagger docs (`/docs`) |
| **Airflow Webserver** | `8080` | HTTP | Pipeline DAG execution & monitoring UI |
| **Polaris REST Catalog** | `8181` | HTTP | Iceberg REST catalog API |
| **Polaris Management** | `8182` | HTTP | Polaris health and management API |
| **Polaris Console** | `8183` | HTTP | Web UI for Iceberg catalog & RBAC |
| **Spark Master UI** | `8082` | HTTP | Spark standalone cluster overview |
| **Spark Master RPC** | `7077` | Spark RPC | Spark cluster submission endpoint |
| **Spark Worker UI** | `8083` | HTTP | Spark worker node status |
| **Trino Query Engine** | `8084` | HTTP | Trino web UI and JDBC/REST query port |
| **Apache Superset** | `8088` | HTTP | BI dashboards and SQL Lab interface |
| **MinIO S3 API** | `9000` | HTTP (S3) | Object storage API endpoint |
| **MinIO Web Console** | `9001` | HTTP | Web management console for S3 buckets |
| **PostgreSQL** | `5432` | TCP | Metadata database for Polaris, Airflow, and Superset |
