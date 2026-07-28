CORE_STAGES = (
    "check_services",
    "capture_mysql_high_cursors",
    "extract_mysql",
    "write_bronze",
    "validate_bronze",
    "build_silver_domain",
    "run_silver_dq",
    "build_gold_dimensions",
    "build_gold_facts",
    "build_gold_marts",
    "reconcile_source_to_gold",
    "publish_analytics_staging",
    "validate_publish",
    "swap_or_upsert_analytics",
    "commit_cursors",
    "publish_pipeline_audit",
)

