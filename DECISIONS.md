# Decisions log

## 2026-07-03 — Sprint 0 skeleton
- Monorepo split into `api/`, `worker/`, `frontend/`, `core/` (empty, shared package for Sprint 1+), `infra/` (empty, Sprint 5).
- FastAPI settings via `pydantic-settings`, env-driven, no hardcoded config.
- Worker runs APScheduler `BackgroundScheduler` in a simple sleep loop rather than a full async event loop; matches the "heartbeat + scheduled jobs" shape needed through Sprint 3 without pulling in extra infra.
- `mypy --strict` on both Python services; added a `tool.mypy.overrides` ignore for `apscheduler.*` since it ships no type stubs, rather than weakening strictness project-wide.
- Frontend scaffolded with `create-next-app` (App Router, TypeScript strict, Tailwind, ESLint) and immediately given a real visual identity (dark terminal aesthetic, IBM Plex Sans/Mono, OKLCH tinted neutrals) instead of shipping the default template — a deliberate scope pull-forward from Sprint 4, approved by the user mid-session. Full page content (dashboard, chat, briefs) still waits for Sprint 4.
- Compose healthchecks: `pg_isready` for postgres, `redis-cli ping` for redis, a bare TCP probe for qdrant (no curl/wget in its image), a Python urllib probe for the API, and a Docker-level `HEALTHCHECK` in the worker's Dockerfile (no HTTP surface to probe otherwise).
