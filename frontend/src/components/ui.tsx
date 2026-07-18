import type { ReactNode } from "react";

/** A titled surface panel — the terminal's basic ledger card. */
export function Panel({
  title,
  meta,
  children,
  className = "",
}: {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`flex flex-col rounded border border-line bg-slate ${className}`}
    >
      <header className="flex items-baseline justify-between border-b border-line px-4 py-2.5">
        <h2 className="font-mono text-[0.7rem] uppercase tracking-[0.18em] text-parchment-dim">
          {title}
        </h2>
        {meta ? (
          <span className="font-mono text-[0.7rem] text-parchment-faint">
            {meta}
          </span>
        ) : null}
      </header>
      <div className="flex-1">{children}</div>
    </section>
  );
}

/** Small uppercase caption. */
export function Label({ children }: { children: ReactNode }) {
  return (
    <span className="font-mono text-[0.65rem] uppercase tracking-[0.18em] text-parchment-faint">
      {children}
    </span>
  );
}

/** Honest empty / error state for a panel body. */
export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="px-4 py-8 text-center font-mono text-xs leading-relaxed text-parchment-faint">
      {children}
    </div>
  );
}
