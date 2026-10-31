CREATE TABLE IF NOT EXISTS lakehouse.gold.dim_date (
    date_key                        INT                             COMMENT 'Date surrogate key YYYYMMDD',
    full_date                       DATE                            COMMENT 'Standard calendar date',
    day_of_week                     INT                             COMMENT 'Day of week (1=Sunday, 7=Saturday)',
    day_name                        STRING                          COMMENT 'Day name (Monday, etc.)',
    day_of_month                    INT                             COMMENT 'Day of month (1-31)',
    day_of_year                     INT                             COMMENT 'Day of year (1-366)',
    week_of_year                    INT                             COMMENT 'ISO week of year (1-53)',
    month                           INT                             COMMENT 'Month number (1-12)',
    month_name                      STRING                          COMMENT 'Month name (January, etc.)',
    quarter                         INT                             COMMENT 'Quarter of year (1-4)',
    year                            INT                             COMMENT 'Calendar year',
    is_weekend                      BOOLEAN                         COMMENT 'True if Saturday or Sunday',
    is_holiday                      BOOLEAN                         COMMENT 'True if recognized public holiday',
    _gold_ingested_at               TIMESTAMP                       COMMENT 'UTC timestamp written to Gold'
)
USING iceberg
PARTITIONED BY (year)
TBLPROPERTIES (
    'format-version' = '2',
    'write.parquet.compression-codec' = 'zstd'
)
