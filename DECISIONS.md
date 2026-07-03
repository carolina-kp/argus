# Decisions log

## 2026-07-03 — Sprint 0 skeleton
- Monorepo split into `api/`, `worker/`, `frontend/`, `core/` (empty, shared package for Sprint 1+), `infra/` (empty, Sprint 5).
- FastAPI settings via `pydantic-settings`, env-driven, no hardcoded config.
- Worker runs APScheduler `BackgroundScheduler` in a simple sleep loop rather than a full async event loop; matches the "heartbeat + scheduled jobs" shape needed through Sprint 3 without pulling in extra infra.
- `mypy --strict` on both Python services; added a `tool.mypy.overrides` ignore for `apscheduler.*` since it ships no type stubs, rather than weakening strictness project-wide.
- Frontend scaffolded with `create-next-app` (App Router, TypeScript strict, Tailwind, ESLint) and immediately given a real visual identity (dark terminal aesthetic, IBM Plex Sans/Mono, OKLCH tinted neutrals) instead of shipping the default template — a deliberate scope pull-forward from Sprint 4, approved by the user mid-session. Full page content (dashboard, chat, briefs) still waits for Sprint 4.
- Compose healthchecks: `pg_isready` for postgres, `redis-cli ping` for redis, a bare TCP probe for qdrant (no curl/wget in its image), a Python urllib probe for the API, and a Docker-level `HEALTHCHECK` in the worker's Dockerfile (no HTTP surface to probe otherwise).

## 2026-07-03 — Sprint 1 market and on-chain data layer
- `core/` is now a real installable package (`argus-core`) holding config, db, models, data clients, cache, repository and the Alembic tree. Both `api` and `worker` depend on it. To make it importable inside each image, the compose build context moved from `./api` / `./worker` to the repo root (`context: .`, `dockerfile: <svc>/Dockerfile`); each Dockerfile installs `./core` first, then the service. This is the standard monorepo shared-package pattern, not a deviation from CLAUDE.md's mandated `core/`.
- Added `argus_core/py.typed` so `mypy --strict` in api/worker treats the shared package as typed rather than erroring on a missing marker.
- Async everywhere: SQLAlchemy 2.0 + asyncpg, async FastAPI sessions. Worker jobs are sync (BackgroundScheduler) and wrap the async collectors in `asyncio.run`, avoiding a second sync DB stack. DATABASE_URL therefore uses the `postgresql+asyncpg://` driver.
- HTTP clients share a `BaseClient`: httpx async, tenacity exponential backoff (retries transport errors and non-2xx incl. 429), and opt-in Redis caching with hard TTLs (CoinGecko current price 60s, historical charts 1h; DeFiLlama 1h; mempool 60s) to stay under CoinGecko's 30 calls/min free limit.
- Snapshot idempotency via Postgres `INSERT ... ON CONFLICT DO NOTHING` on `(coingecko_id, ts)` and `(defillama_slug, ts)` unique constraints, so re-runs and the backfill never duplicate rows.
- Exit test needs 30 days of history immediately, but snapshot jobs only accumulate going forward. Added an idempotent `worker/app/backfill.py` (`python -m app.backfill`) that pulls 30 days of daily price/TVL history from the free historical endpoints, seeding the tables up front.
- Alembic env runs async (`async_engine_from_config` + `run_sync`); the worker applies `alembic upgrade head` on container start before scheduling, so migrations own the schema from the first table.
- Auth is a single-user bearer token dependency applied per-router (`/health` stays open). Designed to swap for real auth later without touching handlers.
- CI gained a `core` job; api/worker jobs `pip install ../core` before their own install. Also added `master` to the push trigger (repo default branch is `master`, Sprint 0 only listed `main`).
