import Link from "next/link";

const ENTRIES = [
  {
    href: "/dashboard",
    tag: "01",
    title: "Dashboard",
    body: "Watchlist with sparklines, DeFi TVL, BTC on-chain metrics, unlock calendar, anomaly badges.",
  },
  {
    href: "/research",
    tag: "02",
    title: "Regulatory Research",
    body: "Ask MiCA and FINMA questions. Every answer traces to a cited article or section — or says it can't.",
  },
  {
    href: "/briefs",
    tag: "03",
    title: "Briefs Archive",
    body: "The daily crypto brief: movers, TVL shifts, unlocks, one regulatory development.",
  },
  {
    href: "/anomalies",
    tag: "04",
    title: "Anomalies Feed",
    body: "Z-score flags on returns, volume, and TVL deltas, plus sustained stablecoin depegs.",
  },
];

export default function Home() {
  return (
    <div className="py-6 sm:py-12">
      <p className="font-mono text-[0.7rem] uppercase tracking-[0.3em] text-seal">
        Swiss / EU digital asset intelligence
      </p>
      <h1 className="mt-5 max-w-3xl font-serif text-4xl font-light leading-[1.1] tracking-tight text-parchment sm:text-6xl">
        Read-only market &amp; regulatory intelligence,{" "}
        <span className="italic text-parchment-dim">cited to origin.</span>
      </h1>
      <p className="mt-6 max-w-xl font-mono text-sm leading-relaxed text-parchment-dim">
        Live crypto markets, DeFi fundamentals, and BTC on-chain data alongside a
        research assistant over MiCA and FINMA guidance. It explains what the
        regulation says — it never advises.
      </p>

      <div className="mt-12 grid gap-px overflow-hidden rounded border border-line bg-line sm:grid-cols-2">
        {ENTRIES.map((entry) => (
          <Link
            key={entry.href}
            href={entry.href}
            className="group flex flex-col gap-3 bg-slate p-6 transition-colors duration-200 hover:bg-slate-2 sm:p-7"
          >
            <div className="flex items-baseline gap-3 font-mono text-xs">
              <span className="text-parchment-faint">{entry.tag}</span>
              <span className="uppercase tracking-widest text-glacier transition-colors group-hover:text-seal">
                {entry.title}
              </span>
            </div>
            <p className="font-mono text-sm leading-relaxed text-parchment-dim">
              {entry.body}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
