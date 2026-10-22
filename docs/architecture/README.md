# Architecture Documents

This directory contains reference architecture documents, logical data schemas, and access logging designs for the D&K E-Commerce Data Platform.

## Table of Contents

- [`SYSTEM_ARCHITECTURE_VISUAL.md`](SYSTEM_ARCHITECTURE_VISUAL.md): Sơ đồ trực quan system context, container architecture, batch/streaming data flow, request sequence, và deployment profiles.
- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md): Container boundaries, dependency rules, directory layout, Python workspace packages, and Docker runtime profiles.
- [`OLTP_SCHEMA.md`](OLTP_SCHEMA.md): Logical schema for 28 MySQL tables, relational constraints, transaction boundaries, concurrency controls, archive logic, and indexing strategies (through migration 0020).
- [`ACCESS_LOG_DESIGN.md`](ACCESS_LOG_DESIGN.md): Structured JSON request log contract, Apache Kafka + Apache Flink streaming pipeline, S3 Landing Zone layout, privacy redactions, and Medallion mapping.
- [`MANAGEMENT_INFO_TECHNICAL_SPEC.md`](MANAGEMENT_INFO_TECHNICAL_SPEC.md): Comprehensive System Analysis & Design (SAD) technical specification for the Management Information System (MIS), dimensional modeling, standardized metrics, and governance rules.
- [`CDC_DASHBOARD_DATA_SPEC.md`](CDC_DASHBOARD_DATA_SPEC.md): Implemented MySQL binlog CDC path, event contract, recovery, verification, and downstream boundary.
- [`../contracts/ecommerce-access-v1.schema.json`](../contracts/ecommerce-access-v1.schema.json): Formal JSON Schema definition for access log records.

Architecture diagrams, deployment topologies, and sequence flows are linked directly within each document.
