import Link from "next/link";
import { ApiError, getAnomalies } from "@/lib/api";
import type { AnomalyItem } from "@/lib/types";
import { EmptyState } from "@/components/ui";
import { AnomalyRow } from "@/components/anomalies/anomaly-row";

export const revalidate = 60;

const KINDS = [
  { value: "", label: "All" },
  { value: "zscore", label: "Z-score" },
  { value: "depeg", label: "Depeg" },
];
const WINDOWS = [
  { value: 1, label: "24h" },
  { value: 7, label: "7d" },
  { value: 30, label: "30d" },
  { value: 90, label: "90d" },
];

function Chip({
  active,
  href,
  children,
}: {
  active: boolean;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "true" : undefined}
      className={`rounded border px-3 py-1.5 font-mono text-xs transition-colors duration-200 ${
        active
          ? "border-seal-dim bg-seal/10 text-seal"
          : "border-line bg-slate text-parchment-dim hover:border-glacier-dim hover:text-parchment"
      }`}
    >
      {children}
    </Link>
  );
}

function href(kind: string, days: number): string {
  const q = new URLSearchParams();
  if (kind) q.set("kind", kind);
  q.set("days", String(days));
  return `/anomalies?${q.toString()}`;
}

export default async function AnomaliesPage({
  searchParams,
}: {
  searchParams: Promise<{ kind?: string; days?: string }>;
}) {
  const params = await searchParams;
  const kind = params.kind === "zscore" || params.kind === "depeg" ? params.kind : "";
  const days = WINDOWS.some((w) => String(w.value) === params.days)
    ? Number(params.days)
    : 7;

  let anomalies: AnomalyItem[] = [];
  let reachable = true;
  try {
    anomalies = await getAnomalies({ kind: kind || undefined, days, limit: 200 });
  } catch (err) {
    if (err instanceof ApiError) reachable = false;
    else throw err;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <p className="font-mono text-[0.7rem] uppercase tracking-[0.3em] text-seal">
          Signal monitor
        </p>
        <h1 className="mt-2 font-serif text-3xl font-light tracking-tight text-parchment sm:text-4xl">
          Anomalies feed
        </h1>
        <p className="mt-3 font-mono text-sm leading-relaxed text-parchment-dim">
          Z-score flags on returns, volume and TVL deltas, plus sustained
          stablecoin depegs. It describes what happened; it does not recommend.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <span className="mr-1 font-mono text-[0.65rem] uppercase tracking-[0.16em] text-parchment-faint">
          Kind
        </span>
        {KINDS.map((k) => (
          <Chip key={k.label} active={kind === k.value} href={href(k.value, days)}>
            {k.label}
          </Chip>
        ))}
        <span className="ml-2 mr-1 font-mono text-[0.65rem] uppercase tracking-[0.16em] text-parchment-faint">
          Window
        </span>
        {WINDOWS.map((w) => (
          <Chip
            key={w.value}
            active={days === w.value}
            href={href(kind, w.value)}
          >
            {w.label}
          </Chip>
        ))}
      </div>

      <section className="rounded border border-line bg-slate">
        <header className="flex items-center justify-between border-b border-line px-4 py-2.5">
          <h2 className="font-mono text-[0.7rem] uppercase tracking-[0.18em] text-parchment-dim">
            Events
          </h2>
          <span className="font-mono text-[0.7rem] text-parchment-faint">
            {anomalies.length} flagged
          </span>
        </header>
        {!reachable ? (
          <EmptyState>Argus API is unreachable.</EmptyState>
        ) : anomalies.length === 0 ? (
          <EmptyState>No anomalies in this window. Quiet markets.</EmptyState>
        ) : (
          <ul>
            {anomalies.map((a) => (
              <AnomalyRow key={a.id} anomaly={a} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
