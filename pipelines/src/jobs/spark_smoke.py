from lakehouse.spark import spark_session

spark = spark_session("probe_spark_chain")
rows = spark.sql("SELECT check_name FROM lakehouse.system.stack_smoke").collect()
assert rows, "không đọc được stack smoke qua Polaris"
print("PROBE1 OK:", [r.check_name for r in rows])
spark.stop()

