"use client";

import { useEffect, useRef, useState } from "react";
import type { Jurisdiction, ResearchAnswer } from "@/lib/types";
import { CitationSeal } from "@/components/research/citation-seal";

type Status = "idle" | "loading" | "done" | "error";

const JURISDICTIONS: { value: Jurisdiction | ""; label: string }[] = [
  { value: "", label: "Any jurisdiction" },
  { value: "EU", label: "EU · MiCA" },
  { value: "CH", label: "CH · FINMA" },
];

const EXAMPLES = [
  "What are the whitepaper requirements for crypto-asset offerings under MiCA?",
  "What does MiCA require of stablecoin (ART/EMT) issuers?",
  "How does FINMA classify a hybrid payment and utility token?",
];

/**
 * Client-side typewriter reveal of an already-returned answer. This is NOT
 * token streaming — the backend returns the complete answer in one response and
 * we reveal it progressively for readability. Reduced-motion users see it whole.
 */
function useReveal(text: string, active: boolean): string {
  // Starts at 0; callers remount per answer (key) so this resets cleanly.
  const [count, setCount] = useState(0);

  useEffect(() => {
    const reduce = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    const instant = !active || reduce || text.length === 0;
    if (instant) {
      // setState only inside an async callback (lint: no set-state-in-effect).
      const id = window.setTimeout(() => setCount(text.length), 0);
      return () => window.clearTimeout(id);
    }
    let current = 0;
    const step = Math.max(1, Math.round(text.length / 240));
    const id = window.setInterval(() => {
      current = Math.min(text.length, current + step);
      setCount(current);
      if (current >= text.length) window.clearInterval(id);
    }, 16);
    return () => window.clearInterval(id);
  }, [text, active]);

  return text.slice(0, count);
}

function AnswerBody({ answer }: { answer: ResearchAnswer }) {
  const revealed = useReveal(answer.answer ?? "", true);
  const complete = revealed.length === (answer.answer?.length ?? 0);

  if (!answer.answered) {
    return (
      <div className="rounded border border-seal-dim bg-seal/5 p-5">
        <p className="font-mono text-[0.7rem] uppercase tracking-[0.16em] text-seal">
          Outside corpus confidence
        </p>
        <p className="mt-2 font-serif text-base leading-relaxed text-parchment-dim">
          {answer.message ??
            "The corpus does not cover this question confidently. No answer given rather than a guess."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="whitespace-pre-wrap font-serif text-lg leading-relaxed text-parchment">
        {revealed}
        {!complete ? <span className="caret" aria-hidden /> : null}
      </div>
      {answer.citations.length > 0 ? (
        <div className="border-t border-line pt-4">
          <p className="mb-3 font-mono text-[0.65rem] uppercase tracking-[0.18em] text-parchment-faint">
            Sources · cited to origin
          </p>
          <div className="flex flex-wrap gap-2">
            {answer.citations.map((c) => (
              <CitationSeal key={c.n} citation={c} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

export default function ResearchPage() {
  const [question, setQuestion] = useState("");
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction | "">("");
  const [status, setStatus] = useState<Status>("idle");
  const [answer, setAnswer] = useState<ResearchAnswer | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asked, setAsked] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  async function submit(q: string) {
    const trimmed = q.trim();
    if (trimmed.length < 8) {
      setError("Enter a question of at least 8 characters.");
      return;
    }
    setStatus("loading");
    setError(null);
    setAnswer(null);
    setAsked(trimmed);
    try {
      const res = await fetch("/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmed,
          jurisdiction: jurisdiction || null,
        }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => null)) as {
          error?: string;
        } | null;
        throw new Error(data?.error ?? `Request failed (${res.status}).`);
      }
      setAnswer((await res.json()) as ResearchAnswer);
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setStatus("error");
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <header>
        <p className="font-mono text-[0.7rem] uppercase tracking-[0.3em] text-seal">
          Regulatory research
        </p>
        <h1 className="mt-2 font-serif text-3xl font-light tracking-tight text-parchment sm:text-4xl">
          Ask MiCA &amp; FINMA
        </h1>
        <p className="mt-3 font-mono text-sm leading-relaxed text-parchment-dim">
          Answers cite the exact article or section and link to the source. It
          explains what the regulation says — it never advises on what to do.
        </p>
      </header>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void submit(question);
        }}
        className="space-y-3"
      >
        <label htmlFor="question" className="sr-only">
          Your regulatory question
        </label>
        <textarea
          id="question"
          ref={textareaRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
              e.preventDefault();
              void submit(question);
            }
          }}
          rows={3}
          placeholder="e.g. What are the whitepaper requirements for crypto-asset offerings under MiCA?"
          className="w-full resize-y rounded border border-line bg-slate px-4 py-3 font-mono text-sm leading-relaxed text-parchment placeholder:text-parchment-faint focus:border-glacier"
        />
        <div className="flex flex-wrap items-center gap-3">
          <label htmlFor="jurisdiction" className="sr-only">
            Jurisdiction filter
          </label>
          <select
            id="jurisdiction"
            value={jurisdiction}
            onChange={(e) =>
              setJurisdiction(e.target.value as Jurisdiction | "")
            }
            className="rounded border border-line bg-slate px-3 py-2 font-mono text-xs text-parchment-dim focus:border-glacier"
          >
            {JURISDICTIONS.map((j) => (
              <option key={j.value} value={j.value} className="bg-slate">
                {j.label}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={status === "loading"}
            className="ml-auto inline-flex items-center gap-2 rounded bg-seal px-4 py-2 font-mono text-xs font-semibold uppercase tracking-wider text-ink transition-opacity duration-200 hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "loading" ? (
              <>
                <span className="h-3 w-3 animate-spin rounded-full border border-ink border-t-transparent" />
                Searching corpus
              </>
            ) : (
              "Ask"
            )}
          </button>
        </div>
        <p className="font-mono text-[0.65rem] text-parchment-faint">
          ⌘/Ctrl + Enter to submit
        </p>
      </form>

      {status === "idle" ? (
        <div className="space-y-2">
          <p className="font-mono text-[0.65rem] uppercase tracking-[0.18em] text-parchment-faint">
            Try
          </p>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setQuestion(ex);
                textareaRef.current?.focus();
              }}
              className="block w-full rounded border border-line bg-slate px-4 py-2.5 text-left font-mono text-xs leading-relaxed text-parchment-dim transition-colors duration-200 hover:border-glacier-dim hover:text-parchment"
            >
              {ex}
            </button>
          ))}
        </div>
      ) : null}

      {error ? (
        <div
          role="alert"
          className="rounded border border-down/40 bg-down/10 px-4 py-3 font-mono text-sm text-down"
        >
          {error}
        </div>
      ) : null}

      {(status === "loading" || status === "done") && asked ? (
        <div className="space-y-5">
          <p className="border-l-2 border-glacier-dim pl-3 font-mono text-xs leading-relaxed text-parchment-dim">
            {asked}
          </p>
          {status === "loading" ? (
            <p className="font-mono text-sm text-parchment-faint">
              Retrieving and generating a cited answer…
            </p>
          ) : answer ? (
            <AnswerBody key={asked} answer={answer} />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
