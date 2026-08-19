# Architecture Documents

This directory contains reference architecture documents, logical data schemas, and access logging designs for the D&K E-Commerce Data Platform.

## Table of Contents

- [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md): Container boundaries, dependency rules, directory layout, Python workspace packages, and Docker runtime profiles.
- [`OLTP_SCHEMA.md`](OLTP_SCHEMA.md): Logical schema for 17 MySQL tables, relational constraints, transaction boundaries, concurrency controls, archive logic, and indexing strategies (migrations 0001–0009).
- [`ACCESS_LOG_DESIGN.md`](ACCESS_LOG_DESIGN.md): Structured JSON request log contract, Fluent Bit 15-minute micro-batch pipeline, S3 Landing Zone layout, privacy redactions, and Medallion mapping.
- [`../contracts/ecommerce-access-v1.schema.json`](../contracts/ecommerce-access-v1.schema.json): Formal JSON Schema definition for access log records.

Architecture diagrams, deployment topologies, and sequence flows are linked directly within each document.
