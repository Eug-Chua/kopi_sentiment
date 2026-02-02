"use client";

import { useState, useRef } from "react";
import { SentimentTimeSeries } from "@/types";
import { MethodologyModal, compositeMethodology } from "./methodology";

interface SentimentChartProps {
  timeseries: SentimentTimeSeries;
  commentary?: string;  // LLM-generated commentary (optional, falls back to dynamic generation)
}

/**
 * Triple-line sentiment chart showing Fears, Frustrations, and Optimism over time.
 * Shows the individual z-score intensity for each emotion category.
 */
export function SentimentChart({ timeseries, commentary: llmCommentary }: SentimentChartProps) {
  const [showMethodology, setShowMethodology] = useState(false);
  const helpButtonRef = useRef<HTMLButtonElement>(null);
  const { data_points, overall_trend, trend_slope, trend_r_squared } = timeseries;

  // Extract 3 separate z-score arrays
  const fearsScores = data_points.map((d) => d.fears_zscore_sum);
  const frustScores = data_points.map((d) => d.frustrations_zscore_sum);
  const optimScores = data_points.map((d) => d.optimism_zscore_sum);

  // Calculate chart dimensions for all scores
  const allScores = [...fearsScores, ...frustScores, ...optimScores];
  const dataMin = Math.min(...allScores, 0);
  const dataMax = Math.max(...allScores);
  const padding = (dataMax - dataMin) * 0.1 || 5;
  const minScore = dataMin - padding;
  const maxScore = dataMax + padding;
  const range = maxScore - minScore || 1;
  const normalize = (value: number) => ((value - minScore) / range) * 100;

  // Current values
  const currentFears = fearsScores[fearsScores.length - 1];
  const currentFrust = frustScores[frustScores.length - 1];
  const currentOptim = optimScores[optimScores.length - 1];
  const prevFears = fearsScores.length > 1 ? fearsScores[fearsScores.length - 2] : currentFears;
  const prevFrust = frustScores.length > 1 ? frustScores[frustScores.length - 2] : currentFrust;
  const prevOptim = optimScores.length > 1 ? optimScores[optimScores.length - 2] : currentOptim;

  // Changes
  const fearsChange = currentFears - prevFears;
  const frustChange = currentFrust - prevFrust;
  const optimChange = currentOptim - prevOptim;

  // Use LLM commentary if available, otherwise generate dynamically
  const commentary = llmCommentary || generateSentimentCommentary(
    currentFears, currentFrust, currentOptim,
    fearsChange, frustChange, optimChange,
    overall_trend
  );

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Methodology Modal */}
      <MethodologyModal
        config={compositeMethodology}
        isOpen={showMethodology}
        onClose={() => setShowMethodology(false)}
        anchorRef={helpButtonRef}
      />

      {/* Header */}
      <div className="p-3 sm:p-5 border-b border-white/[0.06]">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <div>
              <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
                Sentiment Pulse
              </p>
              <p className="text-xs text-white/30 mt-0.5">Z-score intensity by category</p>
            </div>
            {/* Z-score info button */}
            <button
              ref={helpButtonRef}
              onClick={() => setShowMethodology(true)}
              className="w-4 h-4 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-[10px] text-white/40 hover:text-white/60 transition-colors"
            >
              ?
            </button>
          </div>

          {/* Trend badge */}
          <div className={`px-2.5 py-1 rounded-md text-xs font-medium ${
            overall_trend === "rising"
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : overall_trend === "falling"
              ? "bg-red-500/10 text-red-400 border border-red-500/20"
              : "bg-white/5 text-white/60 border border-white/10"
          }`}>
            {overall_trend === "rising" ? "↗ Bullish" : overall_trend === "falling" ? "↘ Bearish" : "→ Neutral"}
          </div>
        </div>

        {/* 3 metric cards */}
        <div className="grid grid-cols-3 gap-2 sm:gap-3 mt-3 sm:mt-4 pt-3 sm:pt-4 border-t border-white/[0.04]">
          <MetricCard
            label="Fears"
            value={currentFears}
            change={fearsChange}
            color="amber"
          />
          <MetricCard
            label="Frustrations"
            value={currentFrust}
            change={frustChange}
            color="red"
          />
          <MetricCard
            label="Optimism"
            value={currentOptim}
            change={optimChange}
            color="emerald"
          />
        </div>

        {/* Commentary - render as bullet points if contains • */}
        <div className="text-sm text-white/60 mt-3 leading-relaxed">
          {commentary.includes("•") ? (
            <ul className="space-y-1.5">
              {commentary.split("•").filter(Boolean).map((line, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-white/30 flex-shrink-0">•</span>
                  <span>{line.trim()}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>{commentary}</p>
          )}
        </div>
      </div>

      {/* Triple line chart */}
      <div className="p-3 sm:p-5 pt-2 sm:pt-3">
        <div className="relative h-24 sm:h-32">
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((pct) => (
            <div
              key={pct}
              className="absolute w-full border-t border-white/[0.04]"
              style={{ bottom: `${pct}%` }}
            />
          ))}

          {/* Zero line */}
          <div
            className="absolute w-full border-t border-white/20 border-dashed"
            style={{ bottom: `${normalize(0)}%` }}
          >
            <span className="absolute right-0 -translate-y-1/2 text-[10px] tabular-nums text-white/30 pr-1">
              0
            </span>
          </div>

          {/* SVG Line Chart */}
          <svg
            className="absolute inset-0 w-full h-full overflow-visible"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
          >
            {/* Fears line (amber) */}
            <path
              d={createLinePath(fearsScores, normalize, data_points.length)}
              fill="none"
              stroke="#f59e0b"
              strokeWidth="0.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
              className="drop-shadow-sm"
            />
            {/* Frustrations line (red) */}
            <path
              d={createLinePath(frustScores, normalize, data_points.length)}
              fill="none"
              stroke="#ef4444"
              strokeWidth="0.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
              className="drop-shadow-sm"
            />
            {/* Optimism line (green) */}
            <path
              d={createLinePath(optimScores, normalize, data_points.length)}
              fill="none"
              stroke="#10b981"
              strokeWidth="0.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
              className="drop-shadow-sm"
            />
          </svg>

          {/* End dots */}
          <div
            className="absolute w-2 h-2 rounded-full bg-amber-500 ring-1 ring-black/50"
            style={{
              right: 0,
              bottom: `${normalize(currentFears)}%`,
              transform: "translate(50%, 50%)",
            }}
          />
          <div
            className="absolute w-2 h-2 rounded-full bg-red-500 ring-1 ring-black/50"
            style={{
              right: 0,
              bottom: `${normalize(currentFrust)}%`,
              transform: "translate(50%, 50%)",
            }}
          />
          <div
            className="absolute w-2 h-2 rounded-full bg-emerald-500 ring-1 ring-black/50"
            style={{
              right: 0,
              bottom: `${normalize(currentOptim)}%`,
              transform: "translate(50%, 50%)",
            }}
          />

          {/* Interactive hover zones */}
          <div className="absolute inset-0 flex">
            {data_points.map((point, index) => (
              <div
                key={point.date}
                className="flex-1 relative group cursor-crosshair"
              >
                {/* Hover line */}
                <div className="absolute inset-y-0 left-1/2 w-px bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity" />

                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                  <div className="bg-[#18181b] border border-white/10 rounded-lg px-3 py-2 shadow-xl shadow-black/50 whitespace-nowrap">
                    <p className="text-[10px] text-white/40 font-medium mb-1">{formatDate(point.date)}</p>
                    <div className="space-y-0.5 text-xs">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-amber-400">Fears</span>
                        <span className="text-amber-400 tabular-nums">{fearsScores[index].toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-red-400">Frust</span>
                        <span className="text-red-400 tabular-nums">{frustScores[index].toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-emerald-400">Optim</span>
                        <span className="text-emerald-400 tabular-nums">{optimScores[index].toFixed(1)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Date labels */}
        <div className="flex justify-between mt-2 text-[10px] text-white/30 tabular-nums">
          <span>{formatDate(data_points[0].date)}</span>
          <span>{formatDate(data_points[data_points.length - 1].date)}</span>
        </div>
      </div>

      {/* Legend and stats */}
      <div className="px-3 sm:px-5 pb-3 sm:pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="flex items-center gap-3 sm:gap-4 text-[10px] sm:text-[11px] text-white/40">
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 rounded-full bg-amber-500" />
              <span>Fears</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 rounded-full bg-red-500" />
              <span>Frustrations</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-3 h-0.5 rounded-full bg-emerald-500" />
              <span>Optimism</span>
            </div>
          </div>
          <div className="flex gap-4 text-[10px]">
            <span className="text-white/30">
              Slope: <span className="text-white/60 tabular-nums">{trend_slope > 0 ? "+" : ""}{trend_slope.toFixed(2)}/d</span>
            </span>
            <span className="text-white/30">
              R²: <span className="text-white/60 tabular-nums">{trend_r_squared.toFixed(3)}</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  change,
  color,
}: {
  label: string;
  value: number;
  change: number;
  color: "amber" | "red" | "emerald";
}) {
  const colorClasses = {
    amber: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    red: "bg-red-500/10 border-red-500/20 text-red-400",
    emerald: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
  }[color];

  return (
    <div className={`rounded-lg p-2.5 border ${colorClasses.split(" ").slice(0, 2).join(" ")}`}>
      <p className="text-[9px] uppercase tracking-wider text-white/40">{label}</p>
      <div className="flex items-baseline gap-1.5 mt-1">
        <span className={`text-base font-medium tabular-nums ${colorClasses.split(" ")[2]}`}>
          {value.toFixed(1)}
        </span>
        <span className={`text-[10px] tabular-nums ${change >= 0 ? "text-white/40" : "text-white/40"}`}>
          {change >= 0 ? "+" : ""}{change.toFixed(1)}
        </span>
      </div>
    </div>
  );
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function createLinePath(values: number[], normalize: (v: number) => number, count: number): string {
  if (count < 2) return "";
  const points = values.map((val, i) => {
    const x = (i / (count - 1)) * 100;
    const y = 100 - normalize(val);
    return `${x},${y}`;
  });
  return `M ${points.join(" L ")}`;
}

/**
 * Generate plain-language commentary about the sentiment data.
 */
function generateSentimentCommentary(
  fears: number,
  frustrations: number,
  optimism: number,
  fearsChange: number,
  frustChange: number,
  optimChange: number,
  trend: string
): string {
  // Find dominant emotion
  const emotions = [
    { name: "Frustrations", value: frustrations, change: frustChange },
    { name: "Fears", value: fears, change: fearsChange },
    { name: "Optimism", value: optimism, change: optimChange },
  ];
  const dominant = emotions.reduce((a, b) => (a.value > b.value ? a : b));

  // Find biggest mover
  const biggestMover = emotions.reduce((a, b) =>
    Math.abs(a.change) > Math.abs(b.change) ? a : b
  );

  // Build commentary with context about what numbers mean
  const parts: string[] = [];

  // Explain the dominant emotion
  if (dominant.name === "Frustrations") {
    parts.push(`Frustrations dominate at ${dominant.value.toFixed(0)} — lots of venting about daily annoyances`);
  } else if (dominant.name === "Fears") {
    parts.push(`Fears lead at ${dominant.value.toFixed(0)} — heightened anxiety in discussions`);
  } else {
    parts.push(`Optimism leads at ${dominant.value.toFixed(0)} — positive sentiment is strongest`);
  }

  // Explain negative values if present
  const negativeEmotions = emotions.filter(e => e.value < 0);
  if (negativeEmotions.length > 0) {
    const negNames = negativeEmotions.map(e => e.name.toLowerCase()).join(" and ");
    parts.push(`(negative ${negNames} means below-average engagement)`);
  }

  // Add trend info if there's a notable mover
  if (Math.abs(biggestMover.change) > 3) {
    const direction = biggestMover.change > 0 ? "rose" : "dropped";
    parts.push(`${biggestMover.name} ${direction} ${Math.abs(biggestMover.change).toFixed(0)} pts from yesterday`);
  }

  return parts.join(". ") + ".";
}
