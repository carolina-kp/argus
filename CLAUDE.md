# Argus: AI Digital Asset Intelligence Terminal

## What this is
A personal digital asset intelligence terminal with an agentic layer, built for the regulated crypto world (Crypto Valley, SDX, Swiss digital asset banks). Three pillars:

1. **Market intelligence**: live crypto market data, DeFi protocol fundamentals (TVL, revenue, flows), BTC on-chain metrics, token unlock calendar.
2. **Regulatory RAG**: a cited question-answering system over MiCA (full EU regulation), FINMA guidance and circulars on token classification, and major protocol whitepapers plus governance documents. Ask "what does MiCA require of stablecoin issuers" or "how does FINMA's token taxonomy treat a hybrid payment/utility token" and get answers with article-level citations.
3. **Agents**: scheduled jobs that produce a daily crypto brief (movers, TVL shifts, unlock events, one regulatory development), scan for anomalies in flows and volumes, and keep the regulatory corpus fresh.

Built by Carolina Kogan Plachkinova (github.com/carolina-kp) as a portfolio-grade project targeting Spring 2027 internships at SIX/SDX, Sygnum, Bitcoin Suisse, Taurus, Crypto Finance AG, and digital-asset desks at private banks. Every decision optimizes for two things: genuinely useful daily, and demonstrably production-grade.

## Non-negotiable principles
1. **Production-grade over feature-rich.** A smaller system with CI/CD, health checks, structured logging, and IaC beats a bigger one deployed by hand. When in doubt, cut a feature, not the ops.
2. **Cited answers only.** The regulatory RAG must return citations at the article/section level (regulation, article number, source URL). If retrieval confidence is low, say so instead of hallucinating. A wrong-but-confident answer about MiCA is the single worst failure mode this project can have.
3. **Free-tier friendly.** Total infra cost target: under 15 EUR/month. One EC2 instance, free API tiers, local embeddings, no per-request managed services.
4. **No fake data, no fake metrics, no advice.** Nothing claims usage or performance that isn't real. Prominent disclaimer: educational project, not financial or legal advice.

## Architecture

```
                        ┌─────────────────────────────────────┐
                        │  EC2 (Docker Compose, Caddy TLS)    │
  ┌──────────┐          │                                     │
  │ Next.js  │──HTTPS──▶│  Caddy ──▶ FastAPI (api)            │
  │ (Vercel) │          │              │                      │
  └──────────┘          │              ├─▶ Postgres (state,   │
                        │              │    watchlist, briefs,│
                        │              │    unlocks, events)  │
                        │              ├─▶ Qdrant (two        │
                        │              │    collections:      │
                        │              │    regulatory, docs) │
                        │              ├─▶ Redis (cache,      │
                        │              │    rate limits)      │
                        │              └─▶ Worker              │
                        │                  (APScheduler jobs) │
                        └─────────────────────────────────────┘
                                       │
        External: CoinGecko, DeFiLlama, mempool.space,
        EUR-Lex (MiCA), finma.ch (guidance PDFs),
        Anthropic API, SMTP (briefs)
```

### Components
- **frontend/**: Next.js 14 + TypeScript + Tailwind on Vercel. Pages: Dashboard (watchlist, TVL panels, BTC on-chain tiles, unlock calendar), Regulatory Research Chat (RAG with article-level citation chips), Briefs archive, Anomalies feed. Dark terminal aesthetic.
- **api/**: FastAPI. REST endpoints, Pydantic models everywhere, async httpx clients with retry/backoff. Auth: single-user token for v1 (env var), designed so proper auth can slot in later.
- **worker/**: APScheduler jobs:
  - `daily_brief` (07:00 CET): watchlist moves, top TVL changes from DeFiLlama, unlocks in next 7 days, plus one retrieval pass over the regulatory collection for any watchlist-relevant development. Generate via Anthropic API, store, email.
  - `market_snapshot` (every 15 min): prices, market caps from CoinGecko; TVL and protocol fees from DeFiLlama (hourly is enough for TVL).
  - `onchain_snapshot` (hourly): mempool fees, hashrate, difficulty from mempool.space.
  - `anomaly_scan` (every 30 min): z-scores on 30-day rolling stats for returns, volume, and TVL deltas; flag |z| > 3; special rule for stablecoin depegs (|price - 1| > 0.005 sustained 3 snapshots). Dedupe, store, surface.
  - `ingest_regulatory` (weekly + manual trigger): fetch and diff regulatory sources, chunk, embed, upsert.
- **infra/**: CloudFormation (VPC, security group, EC2 with UserData bootstrapping Docker), docker-compose.yml for all services. GitHub Actions: lint + typecheck + test on PR; build, push to GHCR, SSH deploy, post-deploy health gate on merge to main.

### Data sources (all free)
- Markets: CoinGecko free API (respect 30 calls/min; cache aggressively in Redis).
- DeFi fundamentals: DeFiLlama API (TVL, fees, revenue, stablecoin supplies; generous and free).
- On-chain BTC: mempool.space public API.
- Token unlocks: DeFiLlama unlocks endpoints where available; otherwise maintain a small curated table for watchlist tokens (be honest in README that this part is curated).
- Regulatory corpus: MiCA from EUR-Lex (Regulation (EU) 2023/1114, HTML version chunks cleanly by article), FINMA ICO guidelines and token classification guidance (PDFs from finma.ch), selected protocol whitepapers and governance docs (BTC, ETH, plus watchlist protocols). All public documents; store source URL and retrieval date per document.
- LLM: Anthropic API. claude-sonnet for briefs and chat, claude-haiku for cheap ingestion tasks (summaries, metadata extraction).
- Embeddings: sentence-transformers locally in worker (bge-small-en-v1.5). Zero embedding cost.

## Regulatory RAG pipeline (the crown jewel)
1. **Ingestion**: parser per source type. MiCA HTML splits on article boundaries (Article N is the natural chunk; long articles split by paragraph with article metadata preserved). FINMA PDFs extracted and split by numbered sections. Whitepapers by heading.
2. **Metadata per chunk**: source (mica | finma | whitepaper), document title, article/section number, jurisdiction (EU | CH), date, source URL.
3. **Embed locally, upsert** to Qdrant collection `regulatory` with payload indexes on source and jurisdiction.
4. **Query path**: rewrite question, dense retrieval top-12 with optional jurisdiction filter, score cutoff, generate with strict prompt requiring inline citations [1][2] that map to (document, article, URL). If max retrieval score is below threshold, respond that the corpus doesn't cover it confidently.
5. **Every query, retrieved set, and answer logged** to Postgres. A small eval set (question, expected article) scores citation hit rate; the real number goes in the README.
6. Hard rule in the system prompt of the RAG chain: it explains what regulations say, it never advises on what a user should do. This distinction matters enormously to the target employers.

## Conventions
- Python: ruff + mypy, pytest, type hints mandatory. Layout: `api/app/`, `worker/app/`, shared `core/` package (models, clients, prompts).
- TypeScript: strict mode, ESLint, no `any`.
- Every service exposes `/health`; compose healthchecks on all containers.
- Structured JSON logging. No print statements.
- Secrets: .env locally, GitHub Actions secrets in CI, never committed.
- Alembic migrations from the first table. Conventional commits.
- Prompt templates live as versioned files in `core/prompts/`, never inline strings.

## Zero-cost mode (active)
This project runs at 0 EUR/month. Constraints:
- **Hosting**: Oracle Cloud Always Free ARM VM (VM.Standard.A1.Flex, up to 4 OCPU / 24 GB RAM) instead of AWS EC2. All images must be ARM64-compatible (everything in this stack is; build multi-arch images in CI). The CloudFormation template in `infra/` stays as a portfolio artifact and a tested deploy path, but the always-on host is Oracle. Fallback if Oracle ARM capacity is unavailable in reachable regions: run everything locally with docker compose and expose the demo via Cloudflare Tunnel (free) only when needed.
- **LLM**: runtime generation (briefs, chat) uses a free-tier API: Google Gemini free tier as primary (daily request quota easily covers one brief per day plus personal chat volume), Groq free tier as fallback. Wrap the LLM behind a single `core/llm.py` interface with a provider switch so Anthropic models can be enabled by env var if a budget ever exists. Prompts stay provider-agnostic.
- **Everything else was already free**: data APIs, local embeddings, Vercel, GitHub Actions, GHCR, email via Gmail app password or Resend free tier.
- README honesty note: state that the system is cloud-portable (CloudFormation for AWS, compose for any Linux host) and currently runs on Oracle's free tier as a deliberate cost decision.

## What NOT to do
- No Kubernetes. Compose on one EC2 is the correct scale.
- No wallet connections, no trading, no transaction execution, no custody of anything. This is read-only intelligence. (Non-negotiable: keeps the project clean legally and signals judgment to regulated employers.)
- No price prediction models presented as signals. Anomaly detection describes what happened; it does not recommend.
- No multi-tenancy or user registration in v1.
- No scraping sources that prohibit it. The listed APIs and public regulatory documents only.
- No gold-plating the frontend before the pipeline works end to end.

## Definition of done (v1)
- `docker compose up` brings up api, worker, postgres, qdrant, redis, caddy locally, all healthy.
- CloudFormation deploys from zero to live URL with one command plus one Actions run.
- Daily brief email arrives with real market data, a real TVL movement, and at least one regulatory retrieval.
- Research chat answers "What are the whitepaper requirements for crypto-asset offerings under MiCA?" with correct article-level citations, verified manually against EUR-Lex.
- Eval script reports real citation hit rate on 15+ questions.
- README with architecture diagram, screenshots, 90-second demo GIF, and an honest tradeoffs section.
