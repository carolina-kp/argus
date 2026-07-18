import type { Metadata } from "next";
import { Spectral, IBM_Plex_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import { NavLink } from "@/components/nav-link";

// Display / prose serif — legal-register authority.
const spectral = Spectral({
  variable: "--font-spectral",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  style: ["normal", "italic"],
});

// Functional mono — all data, tables, tickers, labels, citation seals.
const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Argus — Digital Asset Intelligence Terminal",
  description:
    "A digital asset intelligence terminal: live market data, DeFi fundamentals, BTC on-chain metrics, and cited regulatory research over MiCA and FINMA guidance.",
};

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/research", label: "Research" },
  { href: "/briefs", label: "Briefs" },
  { href: "/anomalies", label: "Anomalies" },
];

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${spectral.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="relative flex min-h-full flex-col">
        {/*
          Signature element — the jurisdiction rail. A persistent left margin,
          EU-blue fading to CH-amber, echoing the ruled margin of a legal text.
          Decorative only, hidden from assistive tech.
        */}
        <span
          aria-hidden
          className="pointer-events-none fixed inset-y-0 left-0 z-20 w-[3px] bg-gradient-to-b from-glacier via-glacier/30 to-seal"
        />

        <header className="sticky top-0 z-10 border-b border-line bg-ink/85 backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-5 py-3.5 sm:px-8">
            <Link
              href="/"
              className="flex items-baseline gap-2 font-mono text-sm tracking-wide"
            >
              <span aria-hidden className="text-seal">
                ◉
              </span>
              <span className="font-semibold text-parchment">ARGUS</span>
              <span className="hidden text-parchment-faint sm:inline">
                / regulatory terminal
              </span>
            </Link>
            <nav
              aria-label="Primary"
              className="flex gap-5 font-mono text-[0.7rem] uppercase tracking-[0.18em] sm:gap-7 sm:text-xs"
            >
              {NAV.map((item) => (
                <NavLink key={item.href} href={item.href} label={item.label} />
              ))}
            </nav>
          </div>
        </header>

        <main className="mx-auto w-full max-w-7xl flex-1 px-5 py-8 sm:px-8 sm:py-12">
          {children}
        </main>

        <footer className="border-t border-line">
          <div className="mx-auto flex max-w-7xl flex-col gap-1 px-5 py-5 font-mono text-[0.7rem] leading-relaxed text-parchment-faint sm:flex-row sm:items-center sm:justify-between sm:px-8">
            <p>
              Educational project. Not financial or legal advice. Read-only
              intelligence — no custody, no trading, no execution.
            </p>
            <p className="text-parchment-faint/70">
              Argus · MiCA + FINMA · sources cited to origin
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
