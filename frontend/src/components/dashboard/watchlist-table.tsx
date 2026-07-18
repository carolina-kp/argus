import type { AnomalyItem, WatchlistItem } from "@/lib/types";
import { Sparkline } from "@/components/sparkline";
import { AnomalyBadge } from "./anomaly-badge";
import { EmptyState } from "@/components/ui";
import { pct, usdPrice } from "@/lib/format";

export interface WatchlistRow {
  item: WatchlistItem;
  spark: number[];
  last: number | null;
  change: number | null;
  anomaly?: AnomalyItem;
}

export function WatchlistTable({ rows }: { rows: WatchlistRow[] }) {
  if (rows.length === 0) {
    return <EmptyState>Watchlist is empty. Seed assets via the API.</EmptyState>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[36rem] border-collapse">
        <thead>
          <tr className="border-b border-line text-left font-mono text-[0.65rem] uppercase tracking-[0.14em] text-parchment-faint">
            <th scope="col" className="px-4 py-2 font-normal">
              Asset
            </th>
            <th scope="col" className="px-4 py-2 text-right font-normal">
              Price
            </th>
            <th scope="col" className="px-4 py-2 text-right font-normal">
              30d
            </th>
            <th scope="col" className="px-4 py-2 text-right font-normal">
              Trend
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ item, spark, last, change, anomaly }) => {
            const up = change != null && change >= 0;
            return (
              <tr
                key={item.id}
                className="border-b border-line/60 transition-colors last:border-0 hover:bg-slate-2"
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-medium text-parchment">
                      {item.symbol}
                    </span>
                    {item.is_stablecoin ? (
                      <span className="rounded-sm border border-line px-1 py-px font-mono text-[0.55rem] uppercase tracking-wider text-parchment-faint">
                        stable
                      </span>
                    ) : null}
                    {anomaly ? <AnomalyBadge anomaly={anomaly} /> : null}
                  </div>
                  <span className="font-mono text-[0.7rem] text-parchment-faint">
                    {item.name}
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-sm tabular text-parchment">
                  {usdPrice(last)}
                </td>
                <td
                  className={`px-4 py-3 text-right font-mono text-sm tabular ${
                    change == null
                      ? "text-parchment-faint"
                      : up
                        ? "text-up"
                        : "text-down"
                  }`}
                >
                  {pct(change)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex justify-end">
                    <Sparkline values={spark} />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
