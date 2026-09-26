import argparse
import sys

from pyspark.sql.functions import col, lit

from lakehouse.logs.bronze import (
    BRONZE_EVENTS_TABLE,
    BRONZE_QUARANTINE_TABLE,
    ensure_bronze_tables,
    transform_corrupt_logs,
    transform_valid_logs,
)
from lakehouse.spark import spark_session

# Iceberg Landing table (written by Flink streaming job)
LANDING_TABLE = "lakehouse.landing.access_logs"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest access logs from Iceberg Landing table to Iceberg Bronze layer"
    )
    parser.add_argument("--run-id", required=True, help="Batch run identifier")
    parser.add_argument("--ingest-date", help="Target UTC date (YYYY-MM-DD)")
    parser.add_argument("--replay-date", help="Replay entire target date (YYYY-MM-DD)")
    args = parser.parse_args()

    if not args.replay_date and not args.ingest_date:
        parser.error("Either --ingest-date or --replay-date must be provided.")

    return args


def main() -> None:
    args = parse_arguments()
    spark = spark_session("ingest_logs_to_bronze")

    # 1. Ensure Polaris namespaces and Iceberg tables exist
    ensure_bronze_tables(spark)

    # 2. Resolve query date
    query_date = args.replay_date or args.ingest_date

    print(f"[{args.run_id}] Reading from Iceberg Landing: {LANDING_TABLE} (date={query_date})")

    # 3. Read from Iceberg Landing (partition-pruned by event_ts)
    #    Landing schema: event_id, event_ts, ingest_ts, service_name,
    #                    http_method, http_route, http_status_code,
    #                    duration_ns, actor_type, ecommerce_action, raw_payload
    try:
        landing_df = (
            spark.read.table(LANDING_TABLE)
            .filter(col("event_ts") >= f"{query_date} 00:00:00")
            .filter(col("event_ts") < f"{query_date} 23:59:59")
            .cache()
        )
    except Exception as exc:
        print(f"[{args.run_id}] Cannot read {LANDING_TABLE}: {exc}")
        spark.stop()
        sys.exit(0)

    total_count = landing_df.count()
    if total_count == 0:
        print(f"[{args.run_id}] No landing rows for {query_date}. Zero-cost No-Op.")
        landing_df.unpersist()
        spark.stop()
        sys.exit(0)

    # 4. Anti-join: exclude event_ids already in Bronze for this date
    if not args.replay_date:
        try:
            committed_ids = (
                spark.read.table(BRONZE_EVENTS_TABLE)
                .filter(col("event_ts") >= f"{query_date} 00:00:00")
                .filter(col("event_ts") < f"{query_date} 23:59:59")
                .select("event_id")
                .distinct()
            )
            unprocessed_df = landing_df.join(committed_ids, on="event_id", how="left_anti")
        except Exception:
            # Bronze table may not exist yet on first run
            unprocessed_df = landing_df
    else:
        unprocessed_df = landing_df

    # 5. Map Landing columns → Bronze-compatible DataFrame
    #    Bronze transform_valid_logs expects OTel-shaped structs; we reconstruct them
    #    inline so the landing flat schema feeds into the existing enrichment function.
    from pyspark.sql.functions import current_timestamp, struct, to_timestamp  # noqa: PLC0415

    bronze_ready_df = (
        unprocessed_df
        .withColumn(
            "schema",
            struct(
                lit("ecommerce.access").alias("name"),
                lit("1.0.0").alias("version"),
            ),
        )
        .withColumn("timestamp", col("event_ts").cast("string"))
        .withColumn("observed_timestamp", col("ingest_ts").cast("string"))
        .withColumn("severity_text",
            (col("http_status_code") >= 500).cast("string"))  # placeholder; enriched below
        .withColumnRenamed("http_status_code", "_http_status_code")
        # Rebuild nested structs expected by transform_valid_logs
        .withColumn("request", struct(col("event_id").alias("id")))
        .withColumn(
            "service",
            struct(
                col("service_name").alias("name"),
                lit("0.1.0").alias("version"),
                lit("production").alias("environment"),
                col("service_name").alias("instance_id"),
            ),
        )
        .withColumn(
            "event",
            struct(
                lit("http.server.request").alias("name"),
                lit("web").alias("category"),
                lit("event").alias("kind"),
                lit("success").alias("outcome"),
                col("duration_ns"),
            ),
        )
        .withColumn(
            "http",
            struct(
                col("http_method").alias("request_method"),
                col("http_route").alias("route"),
                col("_http_status_code").alias("status_code"),
            ),
        )
        .withColumn(
            "actor",
            struct(
                col("actor_type").alias("type"),
                lit(None).cast("string").alias("key"),
            ),
        )
        .withColumn(
            "ecommerce",
            struct(
                col("ecommerce_action").alias("action"),
                lit(None).cast("string").alias("product_key"),
                lit(None).cast("string").alias("variant_key"),
                lit(None).cast("string").alias("search_query"),
                lit(None).cast("boolean").alias("search_redacted"),
                lit(None).cast("map<string,string>").alias("filters"),
            ),
        )
        .withColumn(
            "error",
            struct(
                lit(None).cast("string").alias("code"),
                lit(None).cast("string").alias("type"),
            ),
        )
        .withColumn("client", struct(lit(None).cast("string").alias("user_agent")))
        .withColumn("trace_id", lit(None).cast("string"))
        .withColumn("span_id", lit(None).cast("string"))
        .withColumn("data_origin", lit("iceberg_landing"))
        .withColumn("severity_number", lit(9))  # INFO default
        .withColumn("severity_text", lit("INFO"))
        .withColumn("_source_file", lit(f"iceberg://{LANDING_TABLE}"))
        .withColumn("_corrupt_record", lit(None).cast("string"))
    )

    new_count = bronze_ready_df.count()
    print(f"[{args.run_id}] Processing {new_count} new landing rows → Bronze")

    if new_count == 0:
        print(f"[{args.run_id}] All landing rows already in Bronze. Zero-cost No-Op.")
        landing_df.unpersist()
        spark.stop()
        sys.exit(0)

    # 6. Transform and write to Bronze
    enriched_df = transform_valid_logs(bronze_ready_df, args.run_id)

    if args.replay_date:
        enriched_df.writeTo(BRONZE_EVENTS_TABLE).overwrite(
            col("event_ts").cast("date") == lit(args.replay_date)
        )
        print(f"[{args.run_id}] Atomically overwritten partition {args.replay_date} in {BRONZE_EVENTS_TABLE}.")
    else:
        enriched_df.writeTo(BRONZE_EVENTS_TABLE).append()
        print(f"[{args.run_id}] Appended {new_count} records to {BRONZE_EVENTS_TABLE}.")

    landing_df.unpersist()
    spark.stop()
    print(f"[{args.run_id}] Bronze log ingestion completed successfully.")


if __name__ == "__main__":
    main()
