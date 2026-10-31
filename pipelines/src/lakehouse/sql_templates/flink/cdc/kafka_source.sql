CREATE TEMPORARY TABLE mysql_cdc_kafka (
    record_key STRING,
    payload STRING,
    topic STRING METADATA FROM 'topic' VIRTUAL,
    kafka_partition INT METADATA FROM 'partition' VIRTUAL,
    kafka_offset BIGINT METADATA FROM 'offset' VIRTUAL,
    kafka_timestamp TIMESTAMP_LTZ(3) METADATA FROM 'timestamp' VIRTUAL
) WITH (
    'connector' = 'kafka',
    'topic-pattern' = {{topic_pattern}},
    'properties.bootstrap.servers' = {{bootstrap_servers}},
    'properties.group.id' = {{group_id}},
    'properties.auto.offset.reset' = 'earliest',
    'scan.startup.mode' = 'group-offsets',
    'key.format' = 'raw',
    'key.fields' = 'record_key',
    'value.format' = 'raw',
    'value.fields-include' = 'EXCEPT_KEY',
    'value.raw.charset' = 'UTF-8'
)
