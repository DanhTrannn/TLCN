CREATE NAMESPACE IF NOT EXISTS lakehouse.system;

CREATE TABLE IF NOT EXISTS lakehouse.system.stack_smoke (
  check_name STRING,
  checked_at_utc TIMESTAMP
) USING iceberg;

INSERT INTO lakehouse.system.stack_smoke
VALUES ('spark_write_through_polaris', current_timestamp());

SELECT check_name, checked_at_utc
FROM lakehouse.system.stack_smoke
ORDER BY checked_at_utc DESC
LIMIT 5;
