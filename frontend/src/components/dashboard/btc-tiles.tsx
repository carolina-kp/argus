import type { OnchainPoint } from "@/lib/types";
import { EmptyState } from "@/components/ui";

function Tile({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit?: string;
}) {
  return (
    <div className="flex flex-col gap-1 px-4 py-3">
      <span className="font-mono text-[0.6rem] uppercase tracking-[0.16em] text-parchment-faint">
        {label}
      </span>
      <span className="font-mono text-lg tabular text-parchment">
        {value}
        {unit ? (
          <span className="ml-1 text-xs text-parchment-dim">{unit}</span>
        ) : null}
      </span>
    </div>
  );
}

const num = (v: number | null, digits = 0) =>
  v == null ? "—" : v.toLocaleString("en-US", { maximumFractionDigits: digits });

export function BtcTiles({ data }: { data: OnchainPoint | null }) {
  if (!data) {
    return <EmptyState>No on-chain snapshot yet.</EmptyState>;
  }
  return (
    <div className="grid grid-cols-2 divide-x divide-y divide-line/60 sm:grid-cols-3 sm:divide-y-0">
      <Tile label="Fastest fee" value={num(data.fastest_fee)} unit="sat/vB" />
      <Tile label="30-min fee" value={num(data.half_hour_fee)} unit="sat/vB" />
      <Tile label="1-hr fee" value={num(data.hour_fee)} unit="sat/vB" />
      <Tile label="Hashrate" value={num(data.hashrate_ehs, 1)} unit="EH/s" />
      <Tile
        label="Difficulty"
        value={
          data.difficulty == null
            ? "—"
            : `${(data.difficulty / 1e12).toFixed(1)}T`
        }
      />
    </div>
  );
}
