import { Sparkline } from "@/components/sparkline";
import { EmptyState } from "@/components/ui";
import { pct, usdCompact } from "@/lib/format";

export interface TvlRow {
  symbol: string;
  name: string;
  tvl: number | null;
  change: number | null;
  spark: number[];
}

export function TvlPanel({ rows }: { rows: TvlRow[] }) {
  if (rows.length === 0) {
    return <EmptyState>No DeFi protocols with TVL on the watchlist.</EmptyState>;
  }
  return (
    <ul className="divide-y divide-line/60">
      {rows.map((row) => {
        const up = row.change != null && row.change >= 0;
        return (
          <li
            key={row.symbol}
            className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-slate-2"
          >
            <div className="min-w-0 flex-1">
              <p className="font-mono text-sm font-medium text-parchment">
                {row.symbol}
              </p>
              <p className="truncate font-mono text-[0.7rem] text-parchment-faint">
                {row.name}
              </p>
            </div>
            <Sparkline values={row.spark} width={72} height={24} />
            <div className="w-24 text-right">
              <p className="font-mono text-sm tabular text-parchment">
                {usdCompact(row.tvl)}
              </p>
              <p
                className={`font-mono text-[0.7rem] tabular ${
                  row.change == null
                    ? "text-parchment-faint"
                    : up
                      ? "text-up"
                      : "text-down"
                }`}
              >
                {pct(row.change)}
              </p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
