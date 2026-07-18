import { Panel } from "@/components/ui";

function SkeletonRows({ n }: { n: number }) {
  return (
    <div className="divide-y divide-line/60">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 px-4 py-3.5">
          <div className="h-3 w-16 animate-pulse rounded bg-slate-2" />
          <div className="ml-auto h-3 w-20 animate-pulse rounded bg-slate-2" />
          <div className="h-6 w-24 animate-pulse rounded bg-slate-2" />
        </div>
      ))}
    </div>
  );
}

export default function DashboardLoading() {
  return (
    <div className="space-y-8">
      <div>
        <div className="h-3 w-40 animate-pulse rounded bg-slate-2" />
        <div className="mt-3 h-8 w-48 animate-pulse rounded bg-slate-2" />
      </div>
      <Panel title="Watchlist" meta="30-day price">
        <SkeletonRows n={6} />
      </Panel>
      <div className="grid gap-8 lg:grid-cols-3">
        <Panel title="DeFi TVL" meta="30-day" className="lg:col-span-2">
          <SkeletonRows n={4} />
        </Panel>
        <Panel title="Unlocks" meta="next 7 days">
          <SkeletonRows n={3} />
        </Panel>
      </div>
    </div>
  );
}
