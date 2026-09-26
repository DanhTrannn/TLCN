-- Enable checkpointing for Iceberg snapshot commits
SET 'execution.checkpointing.interval' = '10s';
SET 'execution.checkpointing.mode' = 'EXACTLY_ONCE';
SET 'state.checkpoints.dir' = 'file:///opt/flink/checkpoints';

-- Register Polaris Catalog
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

-- Define Kafka Source Table
CREATE TABLE kafka_access_logs (
    `timestamp` STRING,
    `request` ROW<`id` STRING>,
    `service` ROW<`name` STRING, `version` STRING, `environment` STRING>,
    `event` ROW<`name` STRING, `duration_ns` BIGINT>,
    `http` ROW<`request_method` STRING, `route` STRING, `status_code` INT>,
    `actor` ROW<`type` STRING, `key` STRING>,
    `ecommerce` ROW<`action` STRING, `product_key` STRING, `variant_key` STRING>
) WITH (
    'connector' = 'kafka',
    'topic' = 'ecommerce.access_logs',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'flink-landing-consumer',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    'json.fail-on-missing-field' = 'false',
    'json.ignore-parse-errors' = 'true'
);

-- Stream from Kafka into Iceberg Landing table
INSERT INTO lakehouse.landing.access_logs
SELECT
    COALESCE(`request`.`id`, 'unknown'),
    TO_TIMESTAMP(SUBSTR(REPLACE(`timestamp`, 'Z', ''), 1, 23)),
    CURRENT_TIMESTAMP,
    COALESCE(`service`.`name`, 'ecommerce-api'),
    COALESCE(`http`.`request_method`, 'UNKNOWN'),
    COALESCE(`http`.`route`, 'UNKNOWN'),
    COALESCE(`http`.`status_code`, 200),
    COALESCE(`event`.`duration_ns`, 0),
    COALESCE(`actor`.`type`, 'anonymous'),
    COALESCE(`ecommerce`.`action`, 'unknown'),
    CONCAT('{"event_id":"', COALESCE(`request`.`id`, ''), '","route":"', COALESCE(`http`.`route`, ''), '"}')
FROM kafka_access_logs;
