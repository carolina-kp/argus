# Argus

A personal digital asset intelligence terminal: crypto market data, DeFi protocol
fundamentals, BTC on-chain metrics, and a cited regulatory research assistant over
MiCA and FINMA guidance. Educational project, not financial or legal advice.

See `CLAUDE.md` for full architecture and `BUILD_PLAN.md` for the sprint roadmap.
See `DECISIONS.md` for a running log of design decisions and why they were made.

## Repo layout

```
frontend/   Next.js 14+ (TypeScript, Tailwind, App Router)
api/        FastAPI service
worker/     APScheduler job runner
core/       Shared Python package (models, clients, prompts) — used from Sprint 1
infra/      IaC (CloudFormation) — added in Sprint 5
```

## Local development

Prerequisites: Docker, Docker Compose.

```bash
cp .env.example .env
docker compose up
```

This brings up `postgres`, `redis`, `qdrant`, `api`, and `worker` with healthchecks.
Once healthy: `curl http://localhost:8000/health`.

### Running services individually

```bash
# api
cd api && pip install ".[dev]" && uvicorn app.main:app --reload

# worker
cd worker && pip install ".[dev]" && python -m app.main

# frontend
cd frontend && npm install && npm run dev
```

### Checks

```bash
cd api    && ruff check . && mypy app && pytest
cd worker && ruff check . && mypy app && pytest
cd frontend && npm run lint
```

Pre-commit hooks (ruff, ruff-format, basic hygiene) run automatically on `git commit`
once installed: `pip install pre-commit && pre-commit install`.
