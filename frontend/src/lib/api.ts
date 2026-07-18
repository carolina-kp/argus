/**
 * Server-side Argus API client. Reads the base URL and bearer token from the
 * environment and must only be imported from Server Components or Route
 * Handlers — the token is never exposed to the browser. Client components that
 * need data go through a Route Handler proxy (see app/api/*).
 */
import type {
  AnomalyItem,
  BriefDetail,
  BriefSummary,
  OnchainPoint,
  PricePoint,
  ResearchAnswer,
  ResearchAsk,
  TvlPoint,
  UnlockPoint,
  WatchlistItem,
} from "./types";

const BASE_URL = process.env.ARGUS_API_URL ?? "http://localhost:8000";
const TOKEN = process.env.ARGUS_API_TOKEN ?? "";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "ApiError";
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Seconds to cache in the Next data cache; 0 disables caching. */
  revalidate?: number;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, revalidate = 0 } = opts;
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${TOKEN}`,
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      next: revalidate > 0 ? { revalidate } : { revalidate: 0 },
    });
  } catch (cause) {
    throw new ApiError(0, `Cannot reach Argus API at ${BASE_URL}`, { cause });
  }

  if (!res.ok) {
    throw new ApiError(res.status, `API ${method} ${path} failed (${res.status})`);
  }
  return (await res.json()) as T;
}

// --- Market & on-chain -----------------------------------------------------

export const getWatchlist = () =>
  request<WatchlistItem[]>("/watchlist", { revalidate: 60 });

export const getPrices = (coingeckoId: string, days = 30) =>
  request<PricePoint[]>(
    `/market/prices/${encodeURIComponent(coingeckoId)}?days=${days}`,
    { revalidate: 300 },
  );

export const getTvl = (defillamaSlug: string, days = 30) =>
  request<TvlPoint[]>(
    `/market/tvl/${encodeURIComponent(defillamaSlug)}?days=${days}`,
    { revalidate: 300 },
  );

export const getBtcLatest = () =>
  request<OnchainPoint>("/onchain/btc/latest", { revalidate: 300 });

export const getUnlocks = (days = 7) =>
  request<UnlockPoint[]>(`/market/unlocks?days=${days}`, { revalidate: 300 });

// --- Research --------------------------------------------------------------

export const askResearch = (ask: ResearchAsk) =>
  request<ResearchAnswer>("/research/ask", { method: "POST", body: ask });

// --- Briefs ----------------------------------------------------------------

export const getBriefs = (limit = 30) =>
  request<BriefSummary[]>(`/briefs?limit=${limit}`, { revalidate: 300 });

export const getBrief = (briefDate: string) =>
  request<BriefDetail>(`/briefs/${encodeURIComponent(briefDate)}`, {
    revalidate: 300,
  });

// --- Anomalies -------------------------------------------------------------

export const getAnomalies = (params: {
  kind?: string;
  days?: number;
  limit?: number;
} = {}) => {
  const q = new URLSearchParams();
  if (params.kind) q.set("kind", params.kind);
  if (params.days) q.set("days", String(params.days));
  if (params.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  return request<AnomalyItem[]>(`/anomalies${qs ? `?${qs}` : ""}`, {
    revalidate: 60,
  });
};
