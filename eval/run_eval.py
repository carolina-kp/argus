#!/usr/bin/env python3
"""Citation-accuracy eval for the Argus regulatory RAG.

Sends a fixed set of regulatory questions to ``POST /research/ask`` on the live
backend and measures how often the *expected* source (document + article/section)
shows up in the returned citations. It reports two honest numbers side by side:

* **Hit rate (lenient)** — the expected reference appears *anywhere* in the
  answer's citations. Rewards retrieval that surfaced the right source at all.
* **Top-1 accuracy (strict)** — the expected reference is the *highest-ranked*
  cited source (the citation with the smallest ``n``, i.e. the best-scoring chunk
  the model actually cited). Rewards getting the single most relevant source first.

Both are computed only over the citations the endpoint returns (it echoes back
just the sources the answer cited, ranked by retrieval position), so they measure
end-to-end citation quality, not raw retrieval recall.

A refusal (``answered=false``) or a missing expected reference counts as a miss.
The script exits non-zero if the backend is unreachable, so a broken run can
never be mistaken for a 0% score. The printed number is real; put it in the README.

Usage::

    API_BASE_URL=http://localhost:8000 API_TOKEN=dev-token python eval/run_eval.py

Environment (with defaults matching the local compose stack):
    API_BASE_URL   base URL of the FastAPI service   (default http://localhost:8000)
    API_TOKEN      bearer token                       (default dev-token)
"""
from __future__ import annotations

import os
import re
import sys
import time
from dataclasses import dataclass, field

import httpx

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")
API_TOKEN = os.environ.get("API_TOKEN", "dev-token")
TIMEOUT = httpx.Timeout(60.0)
# The runtime LLM is a free tier with tight per-minute limits. Pace requests and
# retry transient 503s so a throttle can't masquerade as a citation miss.
PACING_SECONDS = float(os.environ.get("EVAL_PACING_SECONDS", "5"))
RETRIES_ON_503 = 3
BACKOFF_SECONDS = 25

# Windows consoles default to cp1252 and choke on non-ASCII; force UTF-8 if we can.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class Case:
    """One eval question.

    ``document`` and ``ref_contains`` describe the expected citation. A citation
    counts as matching when its document contains ``document`` (case-insensitive)
    AND its ref contains ``ref_contains`` after normalisation. ``ref_contains``
    empty means "any section of that document is acceptable" — used where the
    right *document* is the honest expectation but pinning an exact section
    number would be brittle (FINMA guidance, whitepaper headings).
    """

    question: str
    document: str
    ref_contains: str = ""
    jurisdiction: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


# 18 questions: 10 MiCA (pinned to specific articles), 5 FINMA, 3 whitepaper.
CASES: list[Case] = [
    # --- MiCA (EU), article-level expectations ------------------------------
    Case("What must a crypto-asset white paper contain under MiCA?",
         "mica", "Article 6", "EU", ("mica", "whitepaper")),
    Case("What are the whitepaper requirements for crypto-asset offerings under MiCA?",
         "mica", "Article 6", "EU", ("mica", "whitepaper")),
    Case("What information must the crypto-asset white paper disclose about the issuer?",
         "mica", "Article 6", "EU", ("mica",)),
    Case("What are the obligations of issuers of asset-referenced tokens under MiCA?",
         "mica", "Article 16", "EU", ("mica", "art")),
    Case("What own funds must issuers of asset-referenced tokens hold under MiCA?",
         "mica", "Article 35", "EU", ("mica", "art")),
    Case("What are the reserve of assets requirements for asset-referenced tokens?",
         "mica", "Article 36", "EU", ("mica", "art")),
    Case("What must an issuer of e-money tokens comply with under MiCA?",
         "mica", "Article 48", "EU", ("mica", "emt")),
    Case("How does MiCA define a crypto-asset?",
         "mica", "Article 3", "EU", ("mica", "definitions")),
    Case("What does MiCA require regarding authorisation of crypto-asset service providers?",
         "mica", "Article 59", "EU", ("mica", "casp")),
    Case("What are the rules on insider dealing and market abuse for crypto-assets under MiCA?",
         "mica", "Article 89", "EU", ("mica", "abuse")),
    # --- FINMA (CH), document-level (section numbering left flexible) --------
    Case("How does FINMA classify tokens into payment, utility and asset tokens?",
         "finma", "", "CH", ("finma", "taxonomy")),
    Case("How does FINMA treat a hybrid payment and utility token?",
         "finma", "", "CH", ("finma", "hybrid")),
    Case("When does FINMA consider a token to be a security?",
         "finma", "", "CH", ("finma", "security")),
    Case("What is FINMA's guidance on stablecoins?",
         "finma", "", "CH", ("finma", "stablecoin")),
    Case("How does FINMA apply anti-money-laundering rules to token issuances?",
         "finma", "", "CH", ("finma", "aml")),
    # --- Whitepapers (protocol docs), document-level ------------------------
    Case("How does Bitcoin prevent double-spending according to its whitepaper?",
         "bitcoin", "", None, ("whitepaper", "btc")),
    Case("What problem does proof-of-work solve in the Bitcoin whitepaper?",
         "bitcoin", "", None, ("whitepaper", "btc")),
    Case("How does the Aave protocol handle liquidations?",
         "aave", "", None, ("whitepaper", "aave")),
]


def _normalise(text: str) -> str:
    """Fold article/section refs to a comparable form: 'Article 6' == 'Art. 6'."""
    text = text.lower().replace("article", "art").replace("art.", "art")
    return re.sub(r"\s+", " ", text).strip()


def _matches(citation: dict, case: Case) -> bool:
    doc = str(citation.get("document", "")).lower()
    if _normalise(case.document) not in _normalise(doc):
        return False
    if not case.ref_contains:
        return True
    return _normalise(case.ref_contains) in _normalise(str(citation.get("ref", "")))


def _evaluate(client: httpx.Client, case: Case) -> dict:
    payload: dict[str, object] = {"question": case.question}
    if case.jurisdiction:
        payload["jurisdiction"] = case.jurisdiction

    for attempt in range(RETRIES_ON_503 + 1):
        resp = client.post(f"{API_BASE_URL}/research/ask", json=payload)
        # 503 = the free-tier LLM is momentarily throttled, not a retrieval miss.
        if resp.status_code == 503 and attempt < RETRIES_ON_503:
            time.sleep(BACKOFF_SECONDS)
            continue
        break
    resp.raise_for_status()
    data = resp.json()

    if not data.get("answered"):
        return {"hit": False, "top1": False, "refused": True,
                "max_score": data.get("max_score"), "citations": []}

    # Citations arrive ranked by retrieval position (n ascending). Top-1 is the
    # smallest-n citation the answer actually cited.
    citations = sorted(data.get("citations", []), key=lambda c: c.get("n", 1_000))
    hit = any(_matches(c, case) for c in citations)
    top1 = bool(citations) and _matches(citations[0], case)
    return {"hit": hit, "top1": top1, "refused": False,
            "max_score": data.get("max_score"), "citations": citations}


def main() -> int:
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    results: list[tuple[Case, dict]] = []

    try:
        with httpx.Client(headers=headers, timeout=TIMEOUT) as client:
            for i, case in enumerate(CASES):
                if i:
                    time.sleep(PACING_SECONDS)  # stay under the free-tier rate limit
                try:
                    results.append((case, _evaluate(client, case)))
                except httpx.HTTPStatusError as exc:
                    print(f"  ! HTTP {exc.response.status_code} for: {case.question[:60]}",
                          file=sys.stderr)
                    results.append((case, {"hit": False, "top1": False,
                                           "refused": False, "error": True,
                                           "max_score": None, "citations": []}))
    except httpx.HTTPError as exc:
        print(f"FATAL: backend unreachable at {API_BASE_URL} ({exc}).", file=sys.stderr)
        print("Bring the stack up (docker compose up) and ingest the corpus first.",
              file=sys.stderr)
        return 2

    print(f"\nArgus RAG citation eval  ·  {API_BASE_URL}  ·  {len(CASES)} questions\n")
    print(f"{'':2}{'expected':<22}{'hit':>5}{'top1':>6}{'score':>8}  question")
    print("-" * 92)
    for case, r in results:
        expected = f"{case.document} {case.ref_contains}".strip()
        hit = "✓" if r["hit"] else ("REF" if r.get("refused") else "·")
        top1 = "✓" if r["top1"] else "·"
        score = f"{r['max_score']:.3f}" if r.get("max_score") is not None else "  —  "
        print(f"{'':2}{expected:<22}{hit:>5}{top1:>6}{score:>8}  {case.question[:44]}")

    n = len(results)
    hits = sum(1 for _, r in results if r["hit"])
    top1s = sum(1 for _, r in results if r["top1"])
    refusals = sum(1 for _, r in results if r.get("refused"))
    print("-" * 92)
    print(f"\n  Hit rate (lenient, expected source cited anywhere):  "
          f"{hits}/{n} = {100 * hits / n:.1f}%")
    print(f"  Top-1 accuracy (expected source cited first):        "
          f"{top1s}/{n} = {100 * top1s / n:.1f}%")
    print(f"  Honest refusals (answered=false):                    {refusals}/{n}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
