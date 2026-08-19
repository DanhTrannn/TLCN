# Testing and Quality Assurance

This document defines the test taxonomy, execution commands, and verification criteria for the D&K E-Commerce Platform.

## Test Taxonomy

| Category | Scope | Tools & Framework | Count | Execution Target |
|---|---|---|---|---|
| **Backend API Tests** | Authentication, cart operations, atomic checkout, permissions, and access logging | `pytest`, FastAPI `TestClient`, SQLite/MySQL in-memory | 63 tests | Host / Container |
| **Generator Tests** | Deterministic distributions, SQL generation, and access log serialization | `pytest`, `faker` | 54 tests | Host / Container |
| **Pipeline Tests** | High watermarks, cursor state, landing paths, and manifest validation | `pytest`, `pyarrow`, `boto3` | 32 tests | Host / Container |
| **Total Python Suite** | Monorepo cross-package unit and integration testing | `pytest` | 149 tests | Host / Container |
| **Frontend Verification** | TypeScript static typing and Next.js production build | `tsc`, Next.js build | 0 errors | Host / Container |
| **Lakehouse Smoke** | Polaris REST catalog, Spark Iceberg writes, and Trino query serving | `lakehouse_smoke.sh` | Bash / Docker | Docker Compose Stack |

---

## Test Execution Commands

### 1. Run Individual Package Tests

```bash
# Backend API tests (63 tests)
uv run --locked --package ecommerce-api --extra dev -- pytest services/ecommerce-api/tests

# Data Generator tests (54 tests)
uv run --locked --package data-generator --extra dev -- pytest generator/tests

# Lakehouse Pipeline tests (32 tests)
PYTHONPATH=pipelines/src uv run --locked --package batch-pipeline --extra dev -- pytest pipelines/tests
```

### 2. Run All Python Tests in Monorepo (149 Tests)

```bash
PYTHONPATH=pipelines/src:generator/src:services/ecommerce-api uv run pytest
```

### 3. Frontend Type Check and Production Build

```bash
npm --prefix apps/storefront run typecheck
npm --prefix apps/storefront run build
```

### 4. Lakehouse Cluster Integration Smoke Test

```bash
./scripts/lakehouse_smoke.sh
```
