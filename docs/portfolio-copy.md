# Portfolio & LinkedIn copy — Argus

Copy blocks for the portfolio site and LinkedIn. Kept in-repo so the positioning is
versioned alongside the code it describes. Facts here trace to the README and DECISIONS.md.

---

## Portfolio site — one-paragraph project description

**Argus — Cited regulatory-research terminal for digital assets**

Argus is a production-grade intelligence terminal for the regulated crypto world, pairing
live market, DeFi and BTC on-chain data with a retrieval-augmented assistant that answers
MiCA and FINMA questions with article-level citations linked to the primary source. Its
defining constraint is trustworthiness: every answer cites the exact article or section, and
when retrieval confidence falls below a calibrated threshold the system says the corpus does
not cover the question rather than inventing an answer. Citation accuracy is measured, not
claimed, by an eval harness that runs against the live backend (currently 83% lenient hit
rate, 56% top-1 over 18 questions), with the honest failure cases reported alongside. The
full stack (Next.js, FastAPI, Postgres, Qdrant, Redis, scheduled agent jobs) ships with
CI/CD, health-gated deploys, multi-arch images and infrastructure-as-code, and runs at
0 EUR/month on an ARM free tier. Read-only by design: no wallets, no trading, no custody.

---

## LinkedIn — "Featured" section rewrite

**Argus: a cited MiCA/FINMA research terminal (portfolio project)**

I built a regulatory-research terminal for digital assets around one principle: for a
compliance-adjacent tool, a confident wrong answer is the worst possible output. So every
answer cites the exact MiCA article or FINMA section and links to EUR-Lex or finma.ch, and
the system refuses honestly when the corpus does not cover a question instead of
hallucinating. I chunk MiCA at article boundaries (all 149, lossless), embed locally at zero
cost, and gate generation on a calibrated retrieval-score cutoff. I also wrote an eval
harness so citation accuracy is a measured number, not a marketing claim.

It is a full production-shaped stack: Next.js + FastAPI + Postgres + Qdrant, scheduled agent
jobs for a daily brief and anomaly detection, CI/CD with health-gated deploys and IaC, all
at 0 EUR/month. Read-only by design: no wallets, no trading, no custody.

Built for the questions I would want to be asked about it. Repo and write-up below.
