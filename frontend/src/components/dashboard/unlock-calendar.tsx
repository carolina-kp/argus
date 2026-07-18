import type { UnlockPoint } from "@/lib/types";
import { EmptyState } from "@/components/ui";
import { fmtDate, usdCompact } from "@/lib/format";

function daysUntil(iso: string): number {
  const ms = new Date(iso).getTime() - Date.now();
  return Math.max(0, Math.ceil(ms / 86_400_000));
}

export function UnlockCalendar({ unlocks }: { unlocks: UnlockPoint[] }) {
  if (unlocks.length === 0) {
    return (
      <EmptyState>No token unlocks scheduled in the next 7 days.</EmptyState>
    );
  }
  return (
    <ul className="divide-y divide-line/60">
      {unlocks.map((u, i) => {
        const inDays = daysUntil(u.unlock_date);
        return (
          <li
            key={`${u.symbol}-${u.unlock_date}-${i}`}
            className="flex items-center gap-3 px-4 py-3"
          >
            <div className="flex w-14 shrink-0 flex-col items-center rounded border border-line bg-ink py-1.5">
              <span className="font-mono text-sm font-semibold tabular text-seal">
                {inDays}
              </span>
              <span className="font-mono text-[0.55rem] uppercase tracking-wider text-parchment-faint">
                {inDays === 1 ? "day" : "days"}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-mono text-sm text-parchment">
                {u.symbol}
                {u.description ? (
                  <span className="text-parchment-faint"> · {u.description}</span>
                ) : null}
              </p>
              <p className="font-mono text-[0.7rem] text-parchment-faint">
                {fmtDate(u.unlock_date)}
              </p>
            </div>
            {u.amount_usd != null ? (
              <span className="font-mono text-sm tabular text-parchment-dim">
                {usdCompact(u.amount_usd)}
              </span>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}
