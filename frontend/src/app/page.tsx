import Link from "next/link";

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

export default function Home() {
  return (
    <div className="py-4 sm:py-10">
      <section className="grid gap-10 lg:grid-cols-[1.4fr_1fr] lg:items-end">
        <div>
          <p className="font-mono text-[0.7rem] uppercase tracking-[0.34em] text-seal">
            Swiss / EU digital asset intelligence
          </p>
          <h1 className="mt-6 font-serif text-5xl font-light leading-[1.02] tracking-[-0.01em] text-parchment sm:text-7xl">
            Read to origin,
            <br />
            <span className="italic text-parchment-dim">never advised.</span>
          </h1>
        </div>
        <p className="max-w-sm font-mono text-sm leading-relaxed text-parchment-dim lg:pb-3">
          Live crypto markets, DeFi fundamentals and BTC on-chain data beside a
          research assistant over MiCA and FINMA guidance. It explains what the
          regulation says. It does not tell you what to do.
        </p>
      </section>

      <nav aria-label="Sections" className="mt-16 border-t border-line-strong">
        {SECTIONS.map((s) => (
          <Link
            key={s.href}
            href={s.href}
            className="group grid grid-cols-[2.5rem_1fr_auto] items-baseline gap-4 border-b border-line py-6 sm:grid-cols-[4rem_1fr_auto] sm:gap-8 sm:py-8"
          >
            <span className="font-serif text-lg text-parchment-faint transition-colors duration-300 group-hover:text-seal sm:text-2xl">
              {s.index}
            </span>
            <div>
              <h2 className="font-serif text-2xl text-parchment transition-colors duration-300 group-hover:text-parchment sm:text-4xl">
                {s.title}
              </h2>
              <p className="mt-2 max-w-xl font-mono text-xs leading-relaxed text-parchment-dim sm:text-sm">
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
