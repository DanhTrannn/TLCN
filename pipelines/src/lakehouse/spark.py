import os
import time
from pathlib import Path

from pyspark.sql import SparkSession

REALM = "POLARIS"
JAR = "/opt/spark/jars/mysql-connector-j.jar"

def _polaris_credentials() -> tuple[str, str]:
    cred_file = Path(os.environ.get("POLARIS_CREDENTIAL_FILE", "/run/polaris/clients.env"))
    for _ in range(120):  # volume chưa sẵn sàng thì chờ (pattern with-polaris-credentials.sh)
        if cred_file.is_file() and cred_file.stat().st_size > 0:
            break
        time.sleep(1)
    env = {}
    for line in cred_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
                v = v[1:-1]
            env[k.strip()] = v
    return env["POLARIS_SPARK_CLIENT_ID"], env["POLARIS_SPARK_CLIENT_SECRET"]


def spark_session(job_name: str):
    client_id, secret = _polaris_credentials()
    builder = SparkSession.builder.appName(job_name) \
        .master(os.environ["SPARK_MASTER_URL"]) \
        .config("spark.jars", JAR) \
        .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
        .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog") \
        .config("spark.sql.catalog.lakehouse.type", "rest") \
        .config("spark.sql.catalog.lakehouse.uri", os.environ["POLARIS_CATALOG_URI"]) \
        .config("spark.sql.catalog.lakehouse.oauth2-server-uri", f"{os.environ['POLARIS_CATALOG_URI']}/v1/oauth/tokens") \
        .config("spark.sql.catalog.lakehouse.warehouse", os.environ["POLARIS_CATALOG_NAME"]) \
        .config("spark.sql.catalog.lakehouse.scope", "PRINCIPAL_ROLE:ALL") \
        .config("spark.sql.catalog.lakehouse.rest.auth.type", "oauth2") \
        .config("spark.sql.catalog.lakehouse.credential", f"{client_id}:{secret}") \
        .config("spark.sql.catalog.lakehouse.header.Polaris-Realm", REALM) \
        .config("spark.sql.catalog.lakehouse.header.X-Iceberg-Access-Delegation", "vended-credentials") \
        .config("spark.sql.catalog.lakehouse.token-refresh-enabled", "true") \
        .config("spark.sql.session.timeZone", "UTC") \
        .config("spark.sql.catalogImplementation", "in-memory") \
        .config("spark.sql.defaultCatalog", os.environ["POLARIS_CATALOG_NAME"]) \
        .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
    return builder.getOrCreate()


def jdbc_url() -> str:
    # mysql+pymysql://user:pass@host:3306/db -> jdbc:mysql://user:pass@host:3306/db
    url = os.environ["MYSQL_ECOMMERCE_READER_URL"]
    return url.replace("mysql+pymysql://", "jdbc:mysql://", 1)