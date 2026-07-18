/**
 * TypeScript mirrors of the FastAPI Pydantic schemas (api/app/schemas.py).
 * Keep these in sync with the backend; they are the single source of shape
 * truth for the frontend.
 */

export interface WatchlistItem {
  id: number;
  symbol: string;
  name: string;
  coingecko_id: string | null;
  defillama_slug: string | null;
  is_stablecoin: boolean;
}

export interface PricePoint {
  ts: string;
  price_usd: number;
  market_cap_usd: number | null;
  volume_24h_usd: number | null;
}

export interface TvlPoint {
  ts: string;
  tvl_usd: number;
}

export interface OnchainPoint {
  ts: string;
  fastest_fee: number | null;
  half_hour_fee: number | null;
  hour_fee: number | null;
  hashrate_ehs: number | null;
  difficulty: number | null;
}

export interface UnlockPoint {
  symbol: string;
  name: string;
  unlock_date: string;
  amount_tokens: number | null;
  amount_usd: number | null;
  description: string | null;
}

export type Jurisdiction = "EU" | "CH" | "GLOBAL";

export interface ResearchAsk {
  question: string;
  jurisdiction?: Jurisdiction | null;
}

export interface Citation {
  n: number;
  document: string;
  ref: string;
  url: string;
  score: number;
}

export interface ResearchAnswer {
  answered: boolean;
  answer: string | null;
  citations: Citation[];
  max_score: number | null;
  message: string | null;
}

export interface BriefSummary {
  id: number;
  brief_date: string;
  emailed_at: string | null;
  created_at: string;
}

export interface BriefDetail extends BriefSummary {
  sections: Record<string, unknown>;
  body_markdown: string;
}

export type AnomalyKind = "zscore" | "depeg";

export interface AnomalyItem {
  id: number;
  kind: string;
  symbol: string;
  metric: string;
  zscore: number | null;
  value: number | null;
  ts: string;
  detail: Record<string, unknown>;
  created_at: string;
}
