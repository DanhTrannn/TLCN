# syntax=docker/dockerfile:1.7
FROM curlimages/curl:8.17.0 AS pipeline-jars
ARG ICEBERG_VERSION=1.10.1
ARG MYSQL_CONNECTOR_VERSION=8.4.0
ARG HADOOP_AWS_VERSION=3.3.4
ARG AWS_SDK_BUNDLE_VERSION=1.12.262
ARG MAVEN_MIRROR=https://repo1.maven.org/maven2
RUN mkdir -p /tmp/jars \
    && curl --fail --location --retry 5 --retry-all-errors --retry-delay 5 \
      -C - --connect-timeout 30 \
      "${MAVEN_MIRROR}/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar" \
      --output /tmp/jars/iceberg-spark-runtime.jar \
    && curl --fail --location --retry 5 --retry-all-errors --retry-delay 5 \
      -C - --connect-timeout 30 \
      "${MAVEN_MIRROR}/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar" \
      --output /tmp/jars/iceberg-aws-bundle.jar \
    && curl --fail --location --retry 5 --retry-all-errors --retry-delay 5 \
      -C - --connect-timeout 30 \
      "${MAVEN_MIRROR}/com/mysql/mysql-connector-j/${MYSQL_CONNECTOR_VERSION}/mysql-connector-j-${MYSQL_CONNECTOR_VERSION}.jar" \
      --output /tmp/jars/mysql-connector-j.jar \
    && curl --fail --location --retry 5 --retry-all-errors --retry-delay 5 \
      -C - --connect-timeout 30 \
      "${MAVEN_MIRROR}/org/apache/hadoop/hadoop-aws/${HADOOP_AWS_VERSION}/hadoop-aws-${HADOOP_AWS_VERSION}.jar" \
      --output /tmp/jars/hadoop-aws.jar \
    && curl --fail --location --retry 5 --retry-all-errors --retry-delay 5 \
      -C - --connect-timeout 30 \
      "${MAVEN_MIRROR}/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_BUNDLE_VERSION}/aws-java-sdk-bundle-${AWS_SDK_BUNDLE_VERSION}.jar" \
      --output /tmp/jars/aws-java-sdk-bundle.jar

FROM apache/airflow:2.10.5-python3.11
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*
COPY --from=pipeline-jars /tmp/jars/*.jar /opt/spark/jars/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /opt/project
COPY --chown=airflow:root pyproject.toml uv.lock .python-version ./
COPY --chown=airflow:root services/ecommerce-api/pyproject.toml services/ecommerce-api/pyproject.toml
COPY --chown=airflow:root generator/pyproject.toml generator/pyproject.toml
COPY --chown=airflow:root pipelines/pyproject.toml pipelines/pyproject.toml
USER airflow
RUN --mount=type=cache,target=/home/airflow/.cache/uv,uid=50000,gid=0 \
    uv export --frozen --no-dev \
        --no-emit-project --no-emit-workspace --no-hashes \
        --package batch-pipeline \
        --output-file /tmp/airflow-requirements.txt \
    && uv pip install --requirement /tmp/airflow-requirements.txt \
    && rm /tmp/airflow-requirements.txt \
    && uv pip install pyspark==3.5.9 pytest==8.4.1 pandas==2.2.3 \
    && cp /opt/spark/jars/*.jar "$(python -c 'import pyspark, os; print(os.path.join(os.path.dirname(pyspark.__file__), "jars"))')/"
