import Link from "next/link";
import { getBriefs, getPrices } from "@/lib/api";
import { fmtDate, usdPrice } from "@/lib/format";

export const revalidate = 120;

const SECTIONS = [
  {
    href: "/dashboard",
    index: "I",
    title: "Dashboard",
    body: "Watchlist with sparklines, DeFi TVL, BTC on-chain metrics, the unlock calendar, anomaly flags.",
  },
  {
    href: "/research",
    index: "II",
    title: "Regulatory Research",
    body: "Ask MiCA and FINMA. Every answer traces to a cited article or section, or says it cannot.",
  },
  {
    href: "/briefs",
    index: "III",
    title: "Briefs Archive",
    body: "The daily dispatch: movers, TVL shifts, unlocks, one regulatory development.",
  },
  {
    href: "/anomalies",
    index: "IV",
    title: "Anomalies Feed",
    body: "Z-score flags on returns, volume and TVL deltas; sustained stablecoin depegs.",
  },
];

/** One real datum for the hero, or null if the API is unreachable. */
async function liveMarker(): Promise<{
  label: string;
  value: string;
} | null> {
  const [priceRes, briefRes] = await Promise.allSettled([
    getPrices("bitcoin", 1),
    getBriefs(1),
  ]);
  if (priceRes.status === "fulfilled" && priceRes.value.length > 0) {
    const latest = priceRes.value[priceRes.value.length - 1];
    return { label: "BTC", value: usdPrice(latest.price_usd) };
  }
  if (briefRes.status === "fulfilled" && briefRes.value.length > 0) {
    return { label: "Latest brief", value: fmtDate(briefRes.value[0].brief_date) };
  }
  return null;
}

export default async function Home() {
  const marker = await liveMarker();

  return (
    <div className="py-2 sm:py-4">
      <section className="grid gap-6 lg:grid-cols-[1.4fr_1fr] lg:items-end">
        <div>
          <div
            className="rise flex items-center gap-3"
            style={{ animationDelay: "80ms" }}
          >
            <p className="font-mono text-[0.7rem] uppercase tracking-[0.34em] text-seal">
              Swiss / EU digital asset intelligence
            </p>
            {marker ? (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-line px-2.5 py-1 font-mono text-[0.65rem] text-parchment-dim">
                <span
                  aria-hidden
                  className="h-1.5 w-1.5 rounded-full bg-up"
                  style={{ boxShadow: "0 0 6px var(--up)" }}
                />
                <span className="text-parchment-faint">{marker.label}</span>
                <span className="tabular text-parchment">{marker.value}</span>
              </span>
            ) : null}
          </div>
          <h1
            className="rise mt-4 font-serif text-5xl font-light leading-[1.0] tracking-[-0.01em] text-parchment sm:text-7xl"
            style={{ animationDelay: "180ms" }}
          >
            Cited to origin.
            <br />
            <span className="italic text-parchment-dim">Never advice.</span>
          </h1>
        </div>
        <p
          className="rise max-w-sm font-mono text-sm leading-relaxed text-parchment-dim lg:pb-2"
          style={{ animationDelay: "300ms" }}
        >
          Live crypto markets, DeFi fundamentals and BTC on-chain data beside a
          research assistant over MiCA and FINMA guidance. It explains what the
          regulation says. It does not tell you what to do.
        </p>
      </section>

      <nav aria-label="Sections" className="mt-8 border-t border-line-strong sm:mt-10">
        {SECTIONS.map((s, i) => (
          <Link
            key={s.href}
            href={s.href}
            style={{ animationDelay: `${420 + i * 90}ms` }}
            className="rise group grid grid-cols-[2.5rem_1fr_auto] items-baseline gap-4 border-b border-line py-5 sm:grid-cols-[4rem_1fr_auto] sm:gap-8 sm:py-6"
          >
            <span className="font-serif text-lg text-parchment-faint transition-colors duration-300 group-hover:text-seal sm:text-2xl">
              {s.index}
            </span>
            <div>
              <h2 className="font-serif text-2xl text-parchment sm:text-4xl">
                {s.title}
              </h2>
              <p className="mt-1.5 max-w-xl font-mono text-xs leading-relaxed text-parchment-dim sm:text-sm">
                {s.body}
              </p>
            </div>
            <span
              aria-hidden
              className="justify-self-end font-mono text-sm text-parchment-faint transition-all duration-300 group-hover:translate-x-1 group-hover:text-seal"
            >
              →
            </span>
          </Link>
        ))}
      </nav>
    </div>
  );
}
