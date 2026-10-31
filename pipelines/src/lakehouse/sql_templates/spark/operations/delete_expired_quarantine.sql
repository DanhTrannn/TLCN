DELETE FROM lakehouse.quarantine.silver_oltp_violations WHERE _quarantined_at < TIMESTAMP {{cutoff_sql}}
