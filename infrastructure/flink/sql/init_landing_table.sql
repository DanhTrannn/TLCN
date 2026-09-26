-- Register Polaris Iceberg Catalog in Flink SQL
CREATE CATALOG lakehouse WITH (
  'type'='iceberg',
  'catalog-type'='rest',
  'uri'='http://polaris:8181/api/catalog',
  'credential'='${POLARIS_FLINK_CLIENT_ID}:${POLARIS_FLINK_CLIENT_SECRET}',
  'warehouse'='lakehouse',
  'scope'='PRINCIPAL_ROLE:ALL',
  'header.Polaris-Realm'='${POLARIS_REALM}',
  'io-impl'='org.apache.iceberg.aws.s3.S3FileIO',
  's3.endpoint'='http://minio:9000',
  's3.path-style-access'='true',
  's3.access-key-id'='minioadmin',
  's3.secret-access-key'='password'
);

USE CATALOG lakehouse;

-- Ensure landing database/namespace exists
CREATE DATABASE IF NOT EXISTS landing;

-- Create Managed Iceberg Landing Table
CREATE TABLE IF NOT EXISTS landing.access_logs (
    event_id            STRING,
    event_ts            TIMESTAMP(6),
    ingest_ts           TIMESTAMP(6),
    service_name        STRING,
    http_method         STRING,
    http_route          STRING,
    http_status_code    INT,
    duration_ns         BIGINT,
    actor_type          STRING,
    ecommerce_action    STRING,
    raw_payload         STRING
)
PARTITIONED BY (service_name)
WITH (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
);
