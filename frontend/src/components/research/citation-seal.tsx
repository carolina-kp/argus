import type { Citation } from "@/lib/types";

/**
 * Signature element — a citation rendered as an official "seal": a numbered
 * mono chip carrying the source document, its article/section ref and a
 * jurisdiction glyph, linking out to the real EUR-Lex / FINMA source URL.
 */

function provenance(document: string): { glyph: string; label: string } {
  const doc = document.toLowerCase();
  if (doc.includes("mica")) return { glyph: "EU", label: "European Union" };
  if (doc.includes("finma")) return { glyph: "CH", label: "Switzerland" };
  return { glyph: "◆", label: "Reference" };
}

export function CitationSeal({ citation }: { citation: Citation }) {
  const { glyph, label } = provenance(citation.document);
  const isCH = glyph === "CH";
  return (
    <a
      href={citation.url}
      target="_blank"
      rel="noopener noreferrer"
      title={`${citation.document} · ${citation.ref} · ${label} · score ${citation.score.toFixed(2)}`}
      className="group inline-flex items-stretch overflow-hidden rounded border border-line bg-ink transition-colors duration-200 hover:border-seal-dim"
    >
      <span className="flex items-center bg-slate px-1.5 font-mono text-[0.65rem] text-parchment-faint">
        [{citation.n}]
      </span>
      <span
        aria-hidden
        className={`flex items-center px-1.5 font-mono text-[0.6rem] font-semibold tracking-wider ${
          isCH ? "text-seal" : "text-glacier"
        }`}
      >
        {glyph}
      </span>
      <span className="flex items-center gap-1.5 px-2 py-1 font-mono text-[0.7rem] text-parchment-dim group-hover:text-parchment">
        <span className="uppercase text-parchment-faint">
          {citation.document}
        </span>
        <span className="text-parchment">{citation.ref}</span>
        <span aria-hidden className="text-parchment-faint group-hover:text-seal">
          ↗
        </span>
      </span>
    </a>
  );
}
