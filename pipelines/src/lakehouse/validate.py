import io
import json
import hashlib

import boto3
import pyarrow.parquet as pq
from botocore.exceptions import ClientError

from lakehouse.landing import FileStats, Manifest, RunPaths, manifest_from_dict, validate_manifest

S3_REGION = "us-east-1"


def s3_client(endpoint: str, access_key: str, secret_key: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=S3_REGION,
    )


def load_manifest(s3, bucket: str, key: str) -> Manifest:
    body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    return manifest_from_dict(json.loads(body))


def parquet_row_count(data: bytes) -> int:
    return pq.ParquetFile(io.BytesIO(data)).metadata.num_rows


def validate_manifest_on_s3(
    s3,
    bucket: str,
    paths: RunPaths,
    load_stats=None,
) -> list[str]:
    key = paths.manifest_key()
    manifest = load_manifest(s3, bucket, key)
    if manifest.run_id != paths.run_id or manifest.table != paths.table:
        return ["manifest identity does not match requested table/run"]
    if any(not f.path.startswith(paths.data_prefix() + "/") or ".." in f.path.split("/") for f in manifest.files):
        return ["manifest file path is outside requested run"]
    if load_stats is None:

        def load_stats(key: str):
            try:
                obj = s3.get_object(Bucket=bucket, Key=key)
            except ClientError as exc:
                if exc.response["Error"]["Code"] in ("NoSuchKey", "404", "NotFound"):
                    return None
                raise
            data = obj["Body"].read()
            return FileStats(len(data), parquet_row_count(data), hashlib.md5(data).hexdigest())

    return validate_manifest(manifest, load_stats)


def validate_run(s3, bucket: str, tables: list[str], extract_date: str, run_id: str) -> dict[str, list[str]]:
    violations_by_table: dict[str, list[str]] = {}
    for table in tables:
        paths = RunPaths(bucket=bucket, table=table, extract_date=extract_date, run_id=run_id)
        violations_by_table[table] = validate_manifest_on_s3(s3, bucket, paths)
    return violations_by_table
