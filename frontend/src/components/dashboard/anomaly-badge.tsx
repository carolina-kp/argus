import type { AnomalyItem } from "@/lib/types";

/**
 * Compact anomaly marker. Depegs read amber (seal), z-score flags read down-red;
 * a glyph plus text so the kind is legible without relying on colour alone.
 */
export function AnomalyBadge({ anomaly }: { anomaly: AnomalyItem }) {
  const isDepeg = anomaly.kind === "depeg";
  const label = isDepeg
    ? "DEPEG"
    : `z ${anomaly.zscore != null ? anomaly.zscore.toFixed(1) : "·"}`;
  return (
    <span
      title={`${anomaly.kind} · ${anomaly.metric}`}
      className={`inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5 font-mono text-[0.6rem] uppercase tracking-wider ${
        isDepeg
          ? "border-seal-dim bg-seal/10 text-seal"
          : "border-down/40 bg-down/10 text-down"
      }`}
    >
      <span aria-hidden>{isDepeg ? "⚑" : "△"}</span>
      {label}
    </span>
  );
}
