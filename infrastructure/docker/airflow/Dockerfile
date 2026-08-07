# syntax=docker/dockerfile:1.7
FROM apache/airflow:2.10.5-python3.11
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /opt/project
COPY --chown=airflow:root pyproject.toml uv.lock .python-version ./
COPY --chown=airflow:root services/ecommerce-api/pyproject.toml services/ecommerce-api/pyproject.toml
COPY --chown=airflow:root generator/pyproject.toml generator/pyproject.toml
USER airflow
RUN --mount=type=cache,target=/home/airflow/.cache/uv,uid=50000,gid=0 \
    uv export --frozen --no-dev \
        --no-emit-project --no-emit-workspace --no-hashes \
        --output-file /tmp/airflow-requirements.txt \
    && uv pip install --requirement /tmp/airflow-requirements.txt \
    && rm /tmp/airflow-requirements.txt
