# syntax=docker/dockerfile:1.7
FROM apache/superset:4.1.2
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

USER root
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /tmp/uv-workspace
COPY pyproject.toml uv.lock .python-version ./
COPY services/ecommerce-api/pyproject.toml services/ecommerce-api/pyproject.toml
COPY generator/pyproject.toml generator/pyproject.toml
COPY pipelines/batch/pyproject.toml pipelines/batch/pyproject.toml
COPY ml/repurchase/pyproject.toml ml/repurchase/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv export --frozen --extra superset-runtime --no-dev \
        --no-emit-project --no-emit-workspace --no-hashes \
        --output-file /tmp/superset-requirements.txt \
    && uv pip install --system --requirement /tmp/superset-requirements.txt \
    && rm /tmp/superset-requirements.txt

WORKDIR /app
USER superset
