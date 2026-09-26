# syntax=docker/dockerfile:1.7
FROM curlimages/curl:8.17.0 AS jars
ARG ICEBERG_VERSION=1.10.1
ARG FLINK_VERSION=1.19
ARG FLINK_KAFKA_VERSION=3.3.0-1.19
ARG HADOOP_VERSION=3.3.4

RUN mkdir -p /tmp/flink-jars \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-flink-runtime-${FLINK_VERSION}/${ICEBERG_VERSION}/iceberg-flink-runtime-${FLINK_VERSION}-${ICEBERG_VERSION}.jar" \
      --output /tmp/flink-jars/iceberg-flink-runtime.jar \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar" \
      --output /tmp/flink-jars/iceberg-aws-bundle.jar \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/${FLINK_KAFKA_VERSION}/flink-sql-connector-kafka-${FLINK_KAFKA_VERSION}.jar" \
      --output /tmp/flink-jars/flink-sql-connector-kafka.jar \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-api/${HADOOP_VERSION}/hadoop-client-api-${HADOOP_VERSION}.jar" \
      --output /tmp/flink-jars/hadoop-client-api.jar \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-client-runtime/${HADOOP_VERSION}/hadoop-client-runtime-${HADOOP_VERSION}.jar" \
      --output /tmp/flink-jars/hadoop-client-runtime.jar

FROM flink:1.19-java17
USER root

# Enable Hadoop S3 plugin
RUN mkdir -p /opt/flink/plugins/s3-fs-hadoop \
    && cp /opt/flink/opt/flink-s3-fs-hadoop-*.jar /opt/flink/plugins/s3-fs-hadoop/

# Copy Iceberg, Kafka, and Hadoop connectors into flink lib
COPY --from=jars /tmp/flink-jars/*.jar /opt/flink/lib/

COPY infrastructure/flink/conf/flink-conf.yaml /opt/flink/conf/flink-conf.yaml
COPY infrastructure/flink/bin/with-polaris-credentials.sh /opt/project/flink/bin/with-polaris-credentials.sh
COPY infrastructure/flink/bin/run-sql.sh /opt/project/flink/bin/run-sql.sh
RUN chmod 0755 /opt/project/flink/bin/with-polaris-credentials.sh /opt/project/flink/bin/run-sql.sh \
    && mkdir -p /opt/flink/checkpoints \
    && chown -R flink:flink /opt/flink/checkpoints /opt/project/flink

USER flink
