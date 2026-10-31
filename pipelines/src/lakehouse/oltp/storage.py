"""Small Hadoop filesystem boundary shared by batch jobs."""

import json


def read_json(spark, uri: str) -> dict:
    path = spark._jvm.org.apache.hadoop.fs.Path(uri)
    fs = path.getFileSystem(spark._jsc.hadoopConfiguration())
    stream = fs.open(path)
    try:
        return json.loads(spark._jvm.org.apache.commons.io.IOUtils.toString(stream, "UTF-8"))
    finally:
        stream.close()


def write_json(spark, uri: str, value: dict) -> None:
    path = spark._jvm.org.apache.hadoop.fs.Path(uri)
    fs = path.getFileSystem(spark._jsc.hadoopConfiguration())
    fs.mkdirs(path.getParent())
    stream = fs.create(path, True)
    try:
        stream.write(json.dumps(value).encode("utf-8"))
    finally:
        stream.close()
