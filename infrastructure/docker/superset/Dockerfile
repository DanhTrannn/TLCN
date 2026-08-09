# syntax=docker/dockerfile:1.7
FROM apache/superset:4.1.2
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

USER root
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never
WORKDIR /tmp/uv-workspace
COPY infrastructure/docker/superset/requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --requirement requirements.txt

WORKDIR /app
USER superset
