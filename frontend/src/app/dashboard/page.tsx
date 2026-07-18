import {
  ApiError,
  getAnomalies,
  getBtcLatest,
  getPrices,
  getTvl,
  getUnlocks,
  getWatchlist,
} from "@/lib/api";
import type { AnomalyItem, OnchainPoint, UnlockPoint } from "@/lib/types";
import { Panel } from "@/components/ui";
import {
  WatchlistTable,
  type WatchlistRow,
} from "@/components/dashboard/watchlist-table";
import { TvlPanel, type TvlRow } from "@/components/dashboard/tvl-panel";
import { BtcTiles } from "@/components/dashboard/btc-tiles";
import { UnlockCalendar } from "@/components/dashboard/unlock-calendar";
import { pctChange } from "@/lib/format";

// Data changes on the backend snapshot cadence, not per request.
export const revalidate = 120;

interface DashboardData {
  watchRows: WatchlistRow[];
  tvlRows: TvlRow[];
  btc: OnchainPoint | null;
  unlocks: UnlockPoint[];
  anomalyCount: number;
  reachable: boolean;
}

/** Most recent anomaly per symbol, for the inline watchlist badge. */
function latestBySymbol(anomalies: AnomalyItem[]): Map<string, AnomalyItem> {
  const map = new Map<string, AnomalyItem>();
  for (const a of anomalies) {
    const seen = map.get(a.symbol);
    if (!seen || new Date(a.ts) > new Date(seen.ts)) map.set(a.symbol, a);
  }
  return map;
}

async function loadDashboard(): Promise<DashboardData> {
  // The watchlist doubles as the reachability probe: if it throws, the API is
  // down and we render an honest banner rather than a broken page.
  let watchlist;
  try {
    watchlist = await getWatchlist();
  } catch (err) {
    if (err instanceof ApiError) {
      return {
        watchRows: [],
        tvlRows: [],
        btc: null,
        unlocks: [],
        anomalyCount: 0,
        reachable: false,
      };
    }
    throw err;
  }

  const [btcRes, unlocksRes, anomaliesRes] = await Promise.allSettled([
    getBtcLatest(),
    getUnlocks(7),
    getAnomalies({ days: 7, limit: 200 }),
  ]);

  const btc = btcRes.status === "fulfilled" ? btcRes.value : null;
  const unlocks = unlocksRes.status === "fulfilled" ? unlocksRes.value : [];
  const anomalies =
    anomaliesRes.status === "fulfilled" ? anomaliesRes.value : [];
  const anomalyMap = latestBySymbol(anomalies);

  // Per-asset price and TVL series in parallel; one failure never blocks others.
  const watchRows: WatchlistRow[] = await Promise.all(
    watchlist.map(async (item): Promise<WatchlistRow> => {
      if (!item.coingecko_id) {
        return { item, spark: [], last: null, change: null };
      }
      try {
        const prices = await getPrices(item.coingecko_id, 30);
        const series = prices.map((p) => p.price_usd);
        return {
          item,
          spark: series,
          last: series.at(-1) ?? null,
          change: pctChange(series[0], series.at(-1)),
          anomaly: anomalyMap.get(item.symbol),
        };
      } catch {
        return {
          item,
          spark: [],
          last: null,
          change: null,
          anomaly: anomalyMap.get(item.symbol),
        };
      }
    }),
  );

  const tvlRows: TvlRow[] = (
    await Promise.all(
      watchlist
        .filter((i) => i.defillama_slug)
        .map(async (item): Promise<TvlRow | null> => {
          try {
            const tvl = await getTvl(item.defillama_slug as string, 30);
            const series = tvl.map((t) => t.tvl_usd);
            if (series.length === 0) return null;
            return {
              symbol: item.symbol,
              name: item.name,
              tvl: series.at(-1) ?? null,
              change: pctChange(series[0], series.at(-1)),
              spark: series,
            };
          } catch {
            return null;
          }
        }),
    )
  )
    .filter((r): r is TvlRow => r !== null)
    .sort((a, b) => (b.tvl ?? 0) - (a.tvl ?? 0));

  return {
    watchRows,
    tvlRows,
    btc,
    unlocks,
    anomalyCount: anomalies.length,
    reachable: true,
  };
}

export default async function DashboardPage() {
  const data = await loadDashboard();

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-[0.7rem] uppercase tracking-[0.3em] text-seal">
            Market intelligence
          </p>
          <h1 className="mt-2 font-serif text-3xl font-light tracking-tight text-parchment sm:text-4xl">
            Dashboard
          </h1>
        </div>
        {data.reachable ? (
          <p className="font-mono text-[0.7rem] text-parchment-faint">
            {data.anomalyCount} anomal{data.anomalyCount === 1 ? "y" : "ies"} in
            the last 7 days
          </p>
        ) : null}
      </div>

      {!data.reachable ? (
        <div
          role="alert"
          className="rounded border border-down/40 bg-down/10 px-4 py-3 font-mono text-sm text-down"
        >
          Argus API is unreachable. Check that the backend is running and
          ARGUS_API_URL / ARGUS_API_TOKEN are set.
        </div>
      ) : null}

      {/* The ledger dominates; everything else is a secondary band below it. */}
      <Panel title="Watchlist" meta="30-day price">
        <WatchlistTable rows={data.watchRows} />
      </Panel>

      <div className="grid gap-8 lg:grid-cols-3">
        <Panel title="DeFi TVL" meta="30-day">
          <TvlPanel rows={data.tvlRows} />
        </Panel>
        <Panel title="Unlocks" meta="next 7 days">
          <UnlockCalendar unlocks={data.unlocks} />
        </Panel>
        <Panel title="BTC on-chain" meta="latest snapshot">
          <BtcTiles data={data.btc} />
        </Panel>
      </div>
    </div>
  );
}
