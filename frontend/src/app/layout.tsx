import type { Metadata } from "next";
import { IBM_Plex_Mono, IBM_Plex_Sans } from "next/font/google";
import "./globals.css";

const plexSans = IBM_Plex_Sans({
  variable: "--font-plex-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Argus — Digital Asset Intelligence",
  description:
    "A digital asset intelligence terminal: market data, DeFi fundamentals, and cited regulatory research over MiCA and FINMA guidance.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${plexSans.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-bg text-text">
        <header className="border-b border-border">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
            <div className="flex items-baseline gap-2 font-mono text-sm tracking-wide">
              <span className="text-accent">◉</span>
              <span className="text-text">ARGUS</span>
              <span className="text-text-muted">: terminal</span>
            </div>
            <nav className="hidden gap-6 font-mono text-xs uppercase tracking-widest text-text-muted sm:flex">
              <span>Dashboard</span>
              <span>Research</span>
              <span>Briefs</span>
              <span>Anomalies</span>
            </nav>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        <footer className="border-t border-border">
          <div className="mx-auto max-w-6xl px-6 py-4 font-mono text-xs text-text-muted">
            Educational project. Not financial or legal advice. Read-only intelligence, no
            custody, no trading.
          </div>
        </footer>
      </body>
    </html>
  );
}
