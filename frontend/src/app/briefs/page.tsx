import Link from "next/link";
import { ApiError, getBriefs } from "@/lib/api";
import type { BriefSummary } from "@/lib/types";
import { EmptyState } from "@/components/ui";
import { fmtDate, isoDate } from "@/lib/format";

export const revalidate = 300;

async function loadBriefs(): Promise<
  { briefs: BriefSummary[]; reachable: boolean }
> {
  try {
    return { briefs: await getBriefs(60), reachable: true };
  } catch (err) {
    if (err instanceof ApiError) return { briefs: [], reachable: false };
    throw err;
  }
}

export default async function BriefsPage() {
  const { briefs, reachable } = await loadBriefs();

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <p className="font-mono text-[0.7rem] uppercase tracking-[0.3em] text-seal">
          Daily dispatch
        </p>
        <h1 className="mt-2 font-serif text-3xl font-light tracking-tight text-parchment sm:text-4xl">
          Briefs archive
        </h1>
        <p className="mt-3 font-mono text-sm leading-relaxed text-parchment-dim">
          The 07:00 CET brief: watchlist movers, TVL shifts, upcoming unlocks and
          one regulatory development.
        </p>
      </header>

      {!reachable ? (
        <div
          role="alert"
          className="rounded border border-down/40 bg-down/10 px-4 py-3 font-mono text-sm text-down"
        >
          Argus API is unreachable.
        </div>
      ) : briefs.length === 0 ? (
        <div className="rounded border border-line bg-slate">
          <EmptyState>
            No briefs yet. The worker generates one each morning.
          </EmptyState>
        </div>
      ) : (
        <ul className="overflow-hidden rounded border border-line">
          {briefs.map((brief) => (
            <li key={brief.id}>
              <Link
                href={`/briefs/${isoDate(brief.brief_date)}`}
                className="flex items-center justify-between gap-4 border-b border-line bg-slate px-4 py-4 transition-colors duration-200 last:border-0 hover:bg-slate-2"
              >
                <div>
                  <p className="font-serif text-lg text-parchment">
                    {fmtDate(brief.brief_date)}
                  </p>
                  <p className="font-mono text-[0.7rem] text-parchment-faint">
                    {brief.emailed_at ? "Emailed" : "Stored"} ·{" "}
                    {isoDate(brief.brief_date)}
                  </p>
                </div>
                <span
                  aria-hidden
                  className="font-mono text-sm text-parchment-faint"
                >
                  →
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
