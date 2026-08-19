# Project Planning and Specifications

This directory contains the foundational specifications, technical scope boundaries, and design plans for the D&K E-Commerce Data Platform.

## Documents

- [`SCOPE.md`](SCOPE.md): System goals, technical boundaries, 16 analytical tables allowlist, privacy redaction rules, KPI metrics, and ML repurchase prediction scope.
- [`LAKEHOUSE_DESIGN_PLAN.md`](LAKEHOUSE_DESIGN_PLAN.md): Medallion architecture roadmap (Bronze, Silver, Gold), Apache Iceberg storage layout, Polaris namespaces, Spark batch ETL flow, and maintenance strategies.
- [`WEB_DESIGN_PLAN.md`](WEB_DESIGN_PLAN.md): E-commerce storefront and FastAPI backend architectural specifications, transaction constraints, and access log telemetry contracts.

## Scope Governance

Any changes to project scope, domain entities, or analytical boundaries must first be reflected in [`SCOPE.md`](SCOPE.md), followed by corresponding updates to schemas, migrations, pipelines, and test suites.
