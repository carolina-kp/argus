/**
 * Hand-rolled SVG sparkline — no charting dependency. Renders a normalised
 * line (optionally with a faint area fill) sized to a viewBox and scaled by the
 * container via width/height. Colour follows trend so it reads without a label.
 */
interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  className?: string;
  /** Override the trend-derived colour. */
  stroke?: string;
}

export function Sparkline({
  values,
  width = 96,
  height = 28,
  className,
  stroke,
}: SparklineProps) {
  if (values.length < 2) {
    return (
      <svg
        width={width}
        height={height}
        className={className}
        role="img"
        aria-label="No price history"
      >
        <line
          x1="0"
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="var(--line-strong)"
          strokeDasharray="2 3"
        />
      </svg>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const stepX = width / (values.length - 1);
  const pad = 2; // keep the stroke off the top/bottom edge

  const points = values.map((v, i) => {
    const x = i * stepX;
    const y = height - pad - ((v - min) / span) * (height - pad * 2);
    return [x, y] as const;
  });

  const line = points
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const area = `${line} L${width},${height} L0,${height} Z`;

  const trendUp = values[values.length - 1] >= values[0];
  const color = stroke ?? (trendUp ? "var(--up)" : "var(--down)");
  const gradientId = `spark-${trendUp ? "up" : "down"}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      preserveAspectRatio="none"
      role="img"
      aria-label={`Price trend ${trendUp ? "up" : "down"} over the period`}
    >
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${gradientId})`} />
      <path
        d={line}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}
