FROM apache/airflow:2.10.5-python3.11

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

USER airflow
COPY --chown=airflow:root pipelines/batch /opt/project/pipelines/batch
COPY --chown=airflow:root ml/repurchase /opt/project/ml/repurchase
RUN pip install --no-cache-dir \
    /opt/project/pipelines/batch \
    /opt/project/ml/repurchase

