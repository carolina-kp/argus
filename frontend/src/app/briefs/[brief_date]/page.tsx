import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getBrief } from "@/lib/api";
import { Markdown } from "@/components/briefs/markdown";
import { fmtDateTime } from "@/lib/format";

export const revalidate = 300;

export default async function BriefDetailPage({
  params,
}: {
  params: Promise<{ brief_date: string }>;
}) {
  const { brief_date } = await params;

  let brief;
  try {
    brief = await getBrief(brief_date);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) notFound();
    if (err instanceof ApiError) {
      return (
        <div className="mx-auto max-w-3xl">
          <div
            role="alert"
            className="rounded border border-down/40 bg-down/10 px-4 py-3 font-mono text-sm text-down"
          >
            Argus API is unreachable.
          </div>
        </div>
      );
    }
    throw err;
  }

  return (
    <article className="mx-auto max-w-3xl space-y-8">
      <div>
        <Link
          href="/briefs"
          className="font-mono text-[0.7rem] uppercase tracking-[0.18em] text-parchment-faint transition-colors hover:text-seal"
        >
          ← Briefs archive
        </Link>
        <h1 className="mt-4 font-serif text-3xl font-light tracking-tight text-parchment sm:text-4xl">
          Daily brief
        </h1>
        <p className="mt-2 font-mono text-[0.7rem] text-parchment-faint">
          {fmtDateTime(brief.brief_date)}
          {brief.emailed_at
            ? ` · emailed ${fmtDateTime(brief.emailed_at)}`
            : " · stored, not emailed"}
        </p>
      </div>

      <div className="rounded border border-line bg-slate p-6 sm:p-8">
        <Markdown source={brief.body_markdown} />
      </div>
    </article>
  );
}
