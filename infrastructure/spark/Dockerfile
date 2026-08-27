# syntax=docker/dockerfile:1.7
FROM curlimages/curl:8.17.0 AS iceberg
ARG ICEBERG_VERSION=1.10.1
RUN mkdir -p /tmp/iceberg \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.5_2.12-${ICEBERG_VERSION}.jar" \
      --output /tmp/iceberg/iceberg-spark-runtime.jar \
    && curl --fail --location --retry 3 \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-aws-bundle/${ICEBERG_VERSION}/iceberg-aws-bundle-${ICEBERG_VERSION}.jar" \
      --output /tmp/iceberg/iceberg-aws-bundle.jar

FROM apache/spark:3.5.9-java17-python3
USER root
COPY --from=iceberg /tmp/iceberg/*.jar /opt/spark/jars/
COPY infrastructure/spark/conf/spark-defaults.conf /opt/project/spark/spark-defaults.conf
COPY infrastructure/spark/bin/with-polaris-credentials.sh /opt/project/spark/with-polaris-credentials.sh
COPY infrastructure/spark/sql /opt/project/spark/sql
RUN chmod 0755 /opt/project/spark/with-polaris-credentials.sh
USER spark
