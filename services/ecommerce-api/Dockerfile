# syntax=docker/dockerfile:1.7
FROM python:3.11.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
COPY services/ecommerce-api/pyproject.toml services/ecommerce-api/pyproject.toml
COPY generator/pyproject.toml generator/pyproject.toml
COPY pipelines/pyproject.toml pipelines/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package ecommerce-api
COPY services/ecommerce-api/app services/ecommerce-api/app
COPY database ./database
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable \
        --reinstall-package ecommerce-api \
        --refresh-package ecommerce-api \
        --package ecommerce-api
EXPOSE 8000
CMD ["sh", "-c", "alembic -c database/alembic.ini upgrade head && python -m database.seeds.seed_catalog && uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log"]
