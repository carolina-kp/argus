# Build context is the repo root so the shared `core` package is available.
FROM python:3.11-slim

WORKDIR /app

COPY core ./core
RUN pip install --no-cache-dir ./core

COPY worker/pyproject.toml ./
RUN pip install --no-cache-dir .

COPY worker/app ./app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "exit(0)"

# Apply migrations, then run the scheduler.
CMD ["sh", "-c", "cd /app/core && alembic upgrade head && cd /app && python -m app.main"]
