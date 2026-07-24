FROM python:3.11.13-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY services/ecommerce-api/pyproject.toml ./
COPY services/ecommerce-api/app ./app
COPY database ./database
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["sh", "-c", "alembic -c database/alembic.ini upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

