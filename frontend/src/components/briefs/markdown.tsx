import type { ReactNode } from "react";
import { Fragment } from "react";

/**
 * Minimal, dependency-free markdown renderer for LLM-generated brief bodies.
 * Handles headings, bullet lists, bold and paragraphs — deliberately small.
 * All text goes through React's escaping, so no raw HTML is injected.
 */

function inline(text: string): ReactNode {
  // Split on **bold** spans, keeping the delimiters' content.
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-parchment">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

export function Markdown({ source }: { source: string }) {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let list: string[] = [];
  let para: string[] = [];
  let key = 0;

  const flushPara = () => {
    if (para.length) {
      blocks.push(
        <p key={key++} className="leading-relaxed text-parchment-dim">
          {inline(para.join(" "))}
        </p>,
      );
      para = [];
    }
  };
  const flushList = () => {
    if (list.length) {
      blocks.push(
        <ul key={key++} className="ml-4 list-disc space-y-1 text-parchment-dim">
          {list.map((item, i) => (
            <li key={i} className="leading-relaxed">
              {inline(item)}
            </li>
          ))}
        </ul>,
      );
      list = [];
    }
  };

  for (const raw of lines) {
    const line = raw.trimEnd();
    const heading = /^(#{1,3})\s+(.*)$/.exec(line);
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);

    if (heading) {
      flushPara();
      flushList();
      const level = heading[1].length;
      const text = heading[2];
      blocks.push(
        level <= 1 ? (
          <h2
            key={key++}
            className="font-serif text-2xl font-normal text-parchment"
          >
            {inline(text)}
          </h2>
        ) : (
          <h3
            key={key++}
            className="font-mono text-[0.7rem] uppercase tracking-[0.18em] text-seal"
          >
            {inline(text)}
          </h3>
        ),
      );
    } else if (bullet) {
      flushPara();
      list.push(bullet[1]);
    } else if (line.trim() === "") {
      flushPara();
      flushList();
    } else {
      flushList();
      para.push(line);
    }
  }
  flushPara();
  flushList();

  return <div className="space-y-4 font-serif text-base">{blocks}</div>;
}
