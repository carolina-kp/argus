import type { AnomalyItem } from "@/lib/types";
import { fmtDateTime } from "@/lib/format";

export function AnomalyRow({ anomaly }: { anomaly: AnomalyItem }) {
  const isDepeg = anomaly.kind === "depeg";
  return (
    <li className="flex items-start gap-4 border-b border-line/60 px-4 py-3.5 last:border-0">
      <span
        aria-hidden
        className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
          isDepeg ? "bg-seal" : "bg-down"
        }`}
      />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
          <span className="font-mono text-sm font-medium text-parchment">
            {anomaly.symbol}
          </span>
          <span
            className={`rounded-sm border px-1.5 py-px font-mono text-[0.6rem] uppercase tracking-wider ${
              isDepeg
                ? "border-seal-dim text-seal"
                : "border-down/40 text-down"
            }`}
          >
            {anomaly.kind}
          </span>
          <span className="font-mono text-[0.7rem] text-parchment-faint">
            {anomaly.metric}
          </span>
        </div>
        <p className="mt-1 font-mono text-[0.7rem] text-parchment-faint">
          {fmtDateTime(anomaly.ts)}
        </p>
      </div>
      <div className="text-right font-mono text-xs tabular">
        {anomaly.zscore != null ? (
          <p className="text-parchment-dim">z {anomaly.zscore.toFixed(2)}</p>
        ) : null}
        {anomaly.value != null ? (
          <p className="text-parchment-faint">
            {anomaly.value.toLocaleString("en-US", {
              maximumFractionDigits: 4,
            })}
          </p>
        ) : null}
      </div>
    </li>
  );
}
