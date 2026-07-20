import type { ReactNode } from "react";
import type { Citation } from "@/lib/types";

/**
 * Minimal renderer for the answer body's markdown subset: paragraphs,
 * `- ` bullet lists, `**bold**` (including standalone-bold section headers),
 * and `[n]` citation markers that link down to the matching seal chip. The
 * backend's prompt only ever produces this subset, so a full markdown
 * library would be overkill.
 */

const INLINE_TOKEN = /(\*\*[^*]+\*\*|\[\d+\])/g;

function renderInline(
  text: string,
  citations: Map<number, Citation>,
  keyPrefix: string,
): ReactNode[] {
  return text
    .split(INLINE_TOKEN)
    .filter((part) => part !== "")
    .map((part, i) => {
      const bold = /^\*\*([^*]+)\*\*$/.exec(part);
      if (bold) {
        return (
          <strong key={`${keyPrefix}-b-${i}`} className="font-semibold text-parchment">
            {bold[1]}
          </strong>
        );
      }
      const cite = /^\[(\d+)\]$/.exec(part);
      if (cite) {
        const n = Number(cite[1]);
        if (citations.has(n)) {
          return (
            <a
              key={`${keyPrefix}-c-${i}`}
              href={`#cite-${n}`}
              className="mx-0.5 align-super font-mono text-[0.65em] font-semibold text-seal no-underline hover:underline"
            >
              [{n}]
            </a>
          );
        }
      }
      return <span key={`${keyPrefix}-t-${i}`}>{part}</span>;
    });
}

export function AnswerMarkdown({
  text,
  citations,
}: {
  text: string;
  citations: Citation[];
}) {
  const citeMap = new Map(citations.map((c) => [c.n, c]));
  const blocks = text.split(/\n{2,}/).filter((b) => b.trim() !== "");

  return (
    <div className="space-y-4">
      {blocks.map((block, bi) => {
        const lines = block
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean);
        const isList = lines.length > 0 && lines.every((l) => /^[-*]\s+/.test(l));

        if (isList) {
          return (
            <ul key={`b-${bi}`} className="list-disc space-y-1.5 pl-5 marker:text-seal">
              {lines.map((line, li) => (
                <li
                  key={`b-${bi}-${li}`}
                  className="font-serif text-lg leading-relaxed text-parchment"
                >
                  {renderInline(line.replace(/^[-*]\s+/, ""), citeMap, `b-${bi}-${li}`)}
                </li>
              ))}
            </ul>
          );
        }

        // A block that is nothing but a single bold run reads as a section header.
        const heading = lines.length === 1 && /^\*\*([^*]+)\*\*:?$/.exec(block.trim());
        if (heading) {
          return (
            <h3
              key={`b-${bi}`}
              className="font-serif text-xl font-semibold text-parchment"
            >
              {heading[1]}
            </h3>
          );
        }

        return (
          <p key={`b-${bi}`} className="font-serif text-lg leading-relaxed text-parchment">
            {renderInline(block.trim(), citeMap, `b-${bi}`)}
          </p>
        );
      })}
    </div>
  );
}
