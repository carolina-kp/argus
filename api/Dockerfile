# Build context is the repo root so the shared `core` package is available.
FROM python:3.11-slim

WORKDIR /app

COPY core ./core
RUN pip install --no-cache-dir ./core

COPY api/pyproject.toml ./
RUN pip install --no-cache-dir .

COPY api/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
