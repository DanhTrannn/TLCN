from lakehouse.spark import spark_session, jdbc_url

spark = spark_session("probe_jdbc")
count = spark.read.format("jdbc") \
    .option("url", jdbc_url()) \
    .option("dbtable", "customers") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .load().count()

print(f"PROBE2 OK: customers count = {count}")
spark.stop()