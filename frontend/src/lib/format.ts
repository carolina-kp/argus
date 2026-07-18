/**
 * Shared display formatters. Kept framework-agnostic so both Server and Client
 * Components can use them.
 */

const USD_COMPACT = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  notation: "compact",
  maximumFractionDigits: 2,
});

const USD_PRECISE = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

/** Compact USD, e.g. $1.2B, $940.5M. */
export function usdCompact(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return USD_COMPACT.format(value);
}

/** Full USD with adaptive precision for sub-dollar prices. */
export function usdPrice(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  if (value !== 0 && Math.abs(value) < 1) {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 6,
    }).format(value);
  }
  return USD_PRECISE.format(value);
}

/** Signed percentage, e.g. +2.34%, -1.10%. */
export function pct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

/** Percentage change between two values, or null if not computable. */
export function pctChange(
  first: number | null | undefined,
  last: number | null | undefined,
): number | null {
  if (first == null || last == null || first === 0) return null;
  return ((last - first) / first) * 100;
}

const DATE = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const DATETIME = new Intl.DateTimeFormat("en-GB", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

export function fmtDate(iso: string): string {
  return DATE.format(new Date(iso));
}

export function fmtDateTime(iso: string): string {
  return DATETIME.format(new Date(iso));
}

/** ISO date (YYYY-MM-DD) used for brief detail routes. */
export function isoDate(iso: string): string {
  return new Date(iso).toISOString().slice(0, 10);
}
