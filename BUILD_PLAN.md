# Argus Build Plan, crypto edition (6 sprints, ~1 per week, July to mid-August)

Each sprint is 2 to 4 Claude Code sessions and ends with something deployed and demoable. Do them in order. Each has an exit test; if a sprint slips, cut scope inside it, never skip the exit test. Backend is front-loaded on purpose: if summer travel eats Sprints 4 to 6, you still have a demoable agentic pipeline after Sprint 3.

Model strategy: Opus 4.8 as daily driver. Fable 5 for Sprint 2 (regulatory RAG) and Sprint 5 (IaC + deploy pipeline) where long multi-stage autonomous work earns the cost.

---

## Sprint 0: Skeleton and CI (1 to 2 days)
Goal: empty but production-shaped repo.

- Monorepo: `frontend/`, `api/`, `worker/`, `core/`, `infra/`, `docker-compose.yml`.
- FastAPI hello-world with `/health`, Pydantic settings from env.
- Worker container with APScheduler heartbeat job logging every minute.
- Postgres + Qdrant + Redis in compose, healthchecks, named volumes.
- GitHub Actions: ruff, mypy, pytest, ESLint on every PR. Fail on lint from day one. Pre-commit hooks.

Exit test: fresh clone, `docker compose up`, all healthy, CI green on a trivial PR.

---

## Sprint 1: Market and on-chain data layer
Goal: real crypto data flowing into Postgres, watchlist CRUD.

- `core/clients/`: CoinGecko, DeFiLlama, mempool.space (async, retry with backoff, Redis caching, respect rate limits; CoinGecko free tier is 30 calls/min, cache hard).
- Schema via Alembic: `watchlist`, `price_snapshots`, `tvl_snapshots`, `onchain_snapshots`, `unlock_events`.
- Jobs: `market_snapshot` (15 min), `onchain_snapshot` (hourly), TVL hourly.
- API: watchlist CRUD, price/TVL/on-chain read endpoints, token auth middleware.
- Seed watchlist: BTC, ETH, SOL, plus 3 to 5 protocols with meaningful TVL (e.g. AAVE, UNI, LINK) and 2 stablecoins (USDC, USDT) for the depeg rule later.

Exit test: curl the API and get 30 days of real price and TVL history for ETH and AAVE, and current BTC mempool fees.

---

## Sprint 2: Regulatory RAG (the crown jewel, use Fable here)
Goal: MiCA and FINMA searchable with article-level citations.

- MiCA ingestion: fetch Regulation (EU) 2023/1114 HTML from EUR-Lex, parse article boundaries, chunk with article metadata. Unit tests on the parser: article count, spot-check known articles.
- FINMA ingestion: download ICO guidelines and token classification guidance PDFs, extract, split by numbered sections.
- Whitepaper ingestion: BTC and ETH whitepapers plus watchlist protocol docs, split by headings.
- Local embeddings (bge-small-en-v1.5), batch upsert to Qdrant `regulatory` collection with payload metadata and indexes.
- `/research/ask`: retrieval with jurisdiction filter, score cutoff with honest "not covered" fallback, generation with mandatory inline citations mapping to (document, article, URL).
- Query/retrieval/answer logging to Postgres.
- System prompt hard rule: explain what the regulation says, never advise.

Exit test: ask "What are the whitepaper requirements for crypto-asset offerings under MiCA?" and manually verify every cited article against EUR-Lex. Then ask something the corpus does not cover and confirm it says so instead of inventing.

This sprint is your interview centerpiece. Keep detailed notes in DECISIONS.md on chunking choices, retrieval failures, and how you fixed them. "How did you chunk MiCA and why" is a question you want to be excited to receive at Sygnum or SDX.

---

## Sprint 3: Agent layer
Goal: the system works for you while you sleep.

- `daily_brief` (07:00 CET): watchlist movers, top TVL changes, unlocks in the next 7 days, one regulatory retrieval pass for watchlist-relevant context. Strict prompt template versioned in `core/prompts/`. Store brief, email via Gmail app password or Resend free tier.
- `anomaly_scan` (30 min): rolling 30-day z-scores in SQL on returns, volume, TVL deltas; flag |z| > 3; stablecoin depeg rule (|price - 1| > 0.005 across 3 consecutive snapshots). Dedupe, store events.
- `ingest_regulatory` weekly job + manual trigger endpoint (fetch, diff, re-embed only changed docs).
- Brief and anomaly read endpoints.

Exit test: receive a real brief email two mornings in a row; anomaly feed shows at least one flagged event (temporarily lower threshold to verify plumbing, then restore).

---

## Sprint 4: Frontend
Goal: something you can screen-record.

- Next.js on Vercel: Dashboard (watchlist with sparklines, TVL panel, BTC on-chain tiles, unlock calendar, anomaly badges), Regulatory Research Chat (streaming answer, citation chips that link to the exact EUR-Lex article or FINMA PDF), Briefs archive, Anomalies feed.
- Read the frontend-design skill before styling. Dark terminal aesthetic, distinctive, not generic AI UI.
- Disclaimer footer on every page: educational project, not financial or legal advice.

Exit test: full flow on your phone: dashboard, today's brief, ask a MiCA question, tap a citation, land on the actual article.

---

## Sprint 5: Deployment + IaC, zero-cost edition (use Fable here)
Goal: live URL at 0 EUR/month, one-command infra, AWS deploy path proven and documented.

- Provision Oracle Cloud Always Free ARM VM (VM.Standard.A1.Flex, 4 OCPU / 24 GB). Sign up early in the sprint: free ARM capacity can take a few attempts to obtain in EU regions, so start this on day one and build other tasks while waiting.
- CI builds multi-arch images (linux/amd64 + linux/arm64) via buildx, push to GHCR.
- Deploy job: SSH to the VM, `docker compose pull && up -d`, post-deploy health gate failing the workflow if `/health` is not 200.
- Caddy TLS on a duckdns subdomain (free).
- Still write the CloudFormation template (VPC, security group, EC2, UserData bootstrap) and test it once end to end on AWS free trial or a briefly-run instance, capture screenshots and the timed redeploy, then tear it down. The IaC skill is demonstrated and documented without an ongoing bill.
- Backups: nightly pg_dump + Qdrant snapshot to the VM's block storage plus a copy pushed to a private GitHub release or Oracle Object Storage free tier.
- Monitoring: Uptime Kuma container.
- Fallback if Oracle capacity never lands: local compose + Cloudflare Tunnel for demos.

Exit test: live URL served from the free VM survives a full redeploy from CI; separately, the documented AWS CloudFormation run shows stack-delete to live-URL in under 30 minutes.

---

## Sprint 6: Polish and portfolio packaging
Goal: hiring-manager-ready for Swiss digital asset employers.

- README: architecture diagram, demo GIF, honest design decisions and tradeoffs section, "what I'd change at 100x scale" section, and a short paragraph on why read-only and why no advice (judgment signal for regulated employers).
- Eval set: 15 to 20 regulatory questions with expected articles; script reports real citation hit rate. Publish the number even if imperfect.
- Portfolio site: flagship position. LinkedIn featured section rewrite. One targeted post about the MiCA RAG design (this is the kind of post SDX/Sygnum people actually engage with).
- Stretch: EU vs CH comparison mode in chat ("how do MiCA and FINMA differ on X"), which the jurisdiction metadata already enables cheaply.

Exit test: send the repo to one technical person cold; they understand it and run it locally from the README alone.

---

## Working rhythm with Claude Code
- Start every session: "Read CLAUDE.md and BUILD_PLAN.md. We are in Sprint N. Current state: {git log --oneline -5, failing tests if any}."
- One sprint task per session max. Commit and push before ending.
- Claude Code proposing anything outside CLAUDE.md scope: no by default.
- Maintain DECISIONS.md: date, decision, why. Free interview prep.

## Cost guardrails (target: 0 EUR/month)
- Hosting: Oracle Always Free ARM VM. No AWS instance left running; the CloudFormation path is tested once, documented, torn down.
- LLM runtime: Gemini free tier primary, Groq free tier fallback, behind the provider switch in `core/llm.py`. Stay within free daily quotas; the daily brief plus personal chat volume fits comfortably.
- Embeddings local, data APIs free, Vercel free, GHCR free, email free tier.
- Claude Code usage is covered by the existing subscription. Fable 5 draws usage credits at roughly double Opus weight; reserve it for Sprints 2 and 5 and use Opus 4.8 otherwise.
- If any provider ever asks for a card beyond identity verification with actual charges, stop and reassess rather than accept a bill.
