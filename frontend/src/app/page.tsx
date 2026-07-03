export default function Home() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-24">
      <p className="font-mono text-xs uppercase tracking-[0.3em] text-accent">
        System status: booting
      </p>
      <h1 className="mt-4 max-w-2xl text-4xl font-medium leading-tight text-text sm:text-5xl">
        Digital asset intelligence,{" "}
        <span className="text-text-muted">read-only, cited, honest.</span>
      </h1>
      <p className="mt-6 max-w-xl font-mono text-sm leading-relaxed text-text-muted">
        Market data, DeFi fundamentals, BTC on-chain metrics, and a regulatory research
        assistant over MiCA and FINMA guidance: every answer traceable to a source
        <span className="scan-caret"></span>
      </p>
      <div className="mt-10 inline-block rounded border border-border bg-bg-raised px-4 py-3 font-mono text-xs text-text-muted">
        pipeline online in a later sprint: dashboard, chat, and briefs land here
      </div>
    </div>
  );
}
