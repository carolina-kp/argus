FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app ./app

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "exit(0)"

CMD ["python", "-m", "app.main"]
