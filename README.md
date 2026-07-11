# Argus

A personal digital asset intelligence terminal: crypto market data, DeFi protocol
fundamentals, BTC on-chain metrics, and a cited regulatory research assistant over
MiCA and FINMA guidance. Educational project, not financial or legal advice.

See `CLAUDE.md` for full architecture and `BUILD_PLAN.md` for the sprint roadmap.
See `DECISIONS.md` for a running log of design decisions and why they were made.

Built with AI-assisted development; all regulatory citations manually verified
against EUR-Lex, and every design decision documented in `DECISIONS.md`.

## Repo layout

```
frontend/   Next.js 14+ (TypeScript, Tailwind, App Router)
api/        FastAPI service (watchlist CRUD, market/on-chain/RAG, briefs, anomalies)
worker/     APScheduler job runner (snapshots, daily brief, anomaly scan, ingestion)
core/       Shared package: config, db, models, data clients, Alembic migrations
infra/      IaC (CloudFormation) — added in Sprint 5
```

## Local development

Prerequisites: Docker, Docker Compose.

```bash
cp .env.example .env
docker compose up
```

This brings up `postgres`, `redis`, `qdrant`, `api`, and `worker` with healthchecks.
The worker applies Alembic migrations (and seeds the watchlist) on start, then schedules
snapshot jobs. Once healthy: `curl http://localhost:8000/health`.

### Data endpoints (bearer token required)

All non-health routes require `Authorization: Bearer $API_TOKEN`.

```bash
TOKEN=dev-token
# Seed 30 days of price/TVL history immediately (otherwise it accrues over time):
docker compose exec worker python -m app.backfill

curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/watchlist"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/market/prices/ethereum?days=30"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/market/tvl/aave?days=30"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/onchain/btc/latest"
```

### Regulatory research (RAG)

The `regulatory` Qdrant collection holds MiCA (all 149 articles, chunked at article
boundaries), FINMA's ICO guidelines and stablecoin supplement (numbered sections),
and the BTC/ETH/AAVE/UNI/LINK whitepapers — embedded locally with bge-small-en-v1.5.
Generation needs one free LLM key in `.env` (`GEMINI_API_KEY` or `GROQ_API_KEY`).

```bash
# Ingest the corpus (first run downloads sources + embedding model, ~5 min):
docker compose exec worker python -m app.ingest

curl -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question": "What must a crypto-asset white paper contain under MiCA?"}' \
  http://localhost:8000/research/ask
```

Answers carry inline citations `[n]` mapped to `citations[]` (document, article/section,
source URL). If retrieval confidence is below the cutoff, the endpoint says the corpus
does not cover the question instead of generating. It explains what regulations say;
it never gives advice. Every query, retrieved set, and answer is logged to `rag_queries`.

### Agent layer (briefs & anomalies)

The worker runs scheduled agents on top of the data layer:

- **`daily_brief`** (07:00 Europe/Zurich): 24h watchlist movers, TVL shifts, unlocks in
  the next 7 days, and one regulatory retrieval pass, generated via the free LLM provider
  with a versioned prompt, stored, and emailed. Email needs `SMTP_USER`, `SMTP_PASSWORD`
  and `BRIEF_RECIPIENT` in `.env` (Gmail app password); without them the brief is still
  stored and the email step is skipped.
- **`anomaly_scan`** (every 30 min): rolling 30-day z-scores on returns, 24h volume and
  TVL deltas (flag `|z| > 3`), plus a stablecoin depeg rule (`|price − 1| > 0.005` across
  3 consecutive snapshots). Events dedupe per asset/metric/day so they don't refire.
- **`ingest_regulatory`** (weekly): re-fetches sources and re-embeds only chunks whose
  text changed (content-hash diff), so unchanged documents are skipped.

```bash
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/briefs"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/briefs/2026-07-11"
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/anomalies?kind=depeg&days=7"

# Trigger a re-ingestion manually (the worker picks it up within a minute):
curl -X POST -H "Authorization: Bearer $TOKEN" "http://localhost:8000/admin/ingest"
```

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
cd core   && ruff check . && mypy argus_core && pytest
cd api    && ruff check . && mypy app && pytest   # api/worker need `pip install ../core` first
cd worker && ruff check . && mypy app && pytest
cd frontend && npm run lint
```

Pre-commit hooks (ruff, ruff-format, basic hygiene) run automatically on `git commit`
once installed: `pip install pre-commit && pre-commit install`.
