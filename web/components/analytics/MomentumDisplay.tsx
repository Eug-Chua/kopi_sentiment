"use client";

import { useState, useRef } from "react";
import { MomentumReport, CategoryMomentum, VelocityReport, VelocityMetric, DailySentimentScore } from "@/types";
import { MethodologyModal, velocityMethodology } from "./methodology";

// --- Reusable Visualization Components ---

interface DivergingBarProps {
  value: number;
  maxValue: number;
  isPositive: boolean;
  color: "emerald" | "red";
  formatValue?: (v: number) => string;
}

/** Horizontal bar that diverges left/right from center baseline */
function DivergingBar({ value, maxValue, isPositive, color, formatValue }: DivergingBarProps) {
  const barWidth = Math.min(Math.abs(value) / maxValue, 1) * 50;
  const colorClass = color === "emerald" ? "bg-emerald-500/70" : "bg-red-500/70";
  const textColorClass = color === "emerald" ? "text-emerald-400" : "text-red-400";
  const displayValue = formatValue ? formatValue(value) : value.toFixed(1);

  return (
    <div className="flex-1">
      <div className="relative h-3 bg-white/5 rounded-full overflow-hidden">
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/20 z-10" />
        <div
          className={`absolute top-0.5 bottom-0.5 rounded-full transition-all ${colorClass}`}
          style={{
            width: `${barWidth}%`,
            left: isPositive ? "50%" : undefined,
            right: !isPositive ? "50%" : undefined,
          }}
        />
      </div>
      <div className="flex justify-between text-[8px] text-white/30 mt-0.5">
        <span>−{maxValue}σ</span>
        <span className={`${textColorClass} font-medium`}>{displayValue}σ</span>
        <span>+{maxValue}σ</span>
      </div>
    </div>
  );
}

// --- Main Components ---

interface MomentumDisplayProps {
  momentum: MomentumReport;
  velocity?: VelocityReport;
  isDaily?: boolean;
  dataPoints?: DailySentimentScore[];
}

// Map category keys to velocity metric names
const categoryToMetricName: Record<string, string> = {
  fears: "fears_zscore_sum",
  frustrations: "frustrations_zscore_sum",
  optimism: "optimism_zscore_sum",
};

/**
 * Category momentum display with trading-app aesthetics.
 * Shows current intensity (z-score sum) and velocity z-score for anomaly detection.
 */
export function MomentumDisplay({ momentum, velocity, isDaily = true, dataPoints }: MomentumDisplayProps) {
  const [showMethodology, setShowMethodology] = useState(false);
  const helpButtonRef = useRef<HTMLButtonElement>(null);

  const categories: {
    key: keyof Pick<MomentumReport, "fears" | "frustrations" | "optimism">;
    label: string;
  }[] = [
    { key: "fears", label: "Fears" },
    { key: "frustrations", label: "Frustrations" },
    { key: "optimism", label: "Optimism" },
  ];

  // Build a map from metric name to velocity data
  const velocityMap = new Map<string, VelocityMetric>();
  if (velocity?.metrics) {
    for (const metric of velocity.metrics) {
      velocityMap.set(metric.metric_name, metric);
    }
  }

  // Calculate aggregated counts for weekly mode
  const aggregatedCounts = !isDaily && dataPoints ? {
    fears: dataPoints.reduce((sum, d) => sum + d.fears_count, 0),
    frustrations: dataPoints.reduce((sum, d) => sum + d.frustrations_count, 0),
    optimism: dataPoints.reduce((sum, d) => sum + d.optimism_count, 0),
  } : null;

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Category Velocity
            </p>
            <p className="text-xs text-white/30 mt-0.5">{isDaily ? "Today's" : "This week's"} change vs historical</p>
          </div>
          <div className="flex items-center gap-3">
            {/* How it works button */}
            <button
              ref={helpButtonRef}
              onClick={() => setShowMethodology(true)}
              className="text-[10px] text-white/40 hover:text-white/60 transition-colors"
            >
              ?
            </button>
            {/* Legend for z-score interpretation */}
            <div className="flex items-center gap-2 text-[9px] text-white/40">
              <span className="text-white/50">|σ|:</span>
              <span className="text-white/50">&lt;1 normal</span>
              <span className="text-amber-400">1-2 notable</span>
              <span className="text-red-400">&gt;2 unusual</span>
            </div>
          </div>
        </div>
      </div>

      {/* Methodology Modal */}
      <MethodologyModal
        config={velocityMethodology}
        isOpen={showMethodology}
        onClose={() => setShowMethodology(false)}
        anchorRef={helpButtonRef}
      />

      {/* Watchlist-style rows */}
      <div className="divide-y divide-white/[0.04]">
        {categories.map(({ key, label }) => {
          const cat = momentum[key] as CategoryMomentum;
          const metricName = categoryToMetricName[key];
          const velocityMetric = velocityMap.get(metricName);
          const isFastestRising = momentum.fastest_rising === key;
          const isFastestFalling = momentum.fastest_falling === key;

          return (
            <MomentumRow
              key={key}
              label={label}
              categoryKey={key}
              data={cat}
              velocityMetric={velocityMetric}
              highlight={isFastestRising ? "rising" : isFastestFalling ? "falling" : null}
              isDaily={isDaily}
              aggregatedCount={aggregatedCounts?.[key]}
            />
          );
        })}
      </div>

      {/* Footer summary */}
      <div className="p-3 border-t border-white/[0.04]">
        <div className="flex items-center justify-between text-[10px]">
          <div className="flex items-center gap-4">
            <span className="text-white/30">Fastest moving:</span>
            <span className="text-emerald-400">
              ↑ {momentum.fastest_rising.charAt(0).toUpperCase() + momentum.fastest_rising.slice(1)}
            </span>
            <span className="text-red-400">
              ↓ {momentum.fastest_falling.charAt(0).toUpperCase() + momentum.fastest_falling.slice(1)}
            </span>
          </div>
        </div>
        <p className="text-[9px] text-white/30 mt-2">
          Velocity σ shows how unusual {isDaily ? "today's" : "this week's"} change is. |σ| &gt; 2 = statistically significant.
        </p>
      </div>
    </div>
  );
}

interface MomentumRowProps {
  label: string;
  categoryKey: "fears" | "frustrations" | "optimism";
  data: CategoryMomentum;
  velocityMetric?: VelocityMetric;
  highlight: "rising" | "falling" | null;
  isDaily?: boolean;
  aggregatedCount?: number;
}

function MomentumRow({ label, categoryKey, data, velocityMetric, highlight, isDaily = true, aggregatedCount }: MomentumRowProps) {
  // Handle missing data gracefully
  if (!data) {
    return (
      <div className="px-4 py-3 flex items-center gap-4 text-white/30 text-xs">
        <span className="text-xs">{label}</span>
        <span>No data available</span>
      </div>
    );
  }

  const count = aggregatedCount ?? data.current_count ?? 0;

  // Get velocity data if available
  const velocityZscore = velocityMetric?.velocity_zscore ?? 0;
  const velocity = velocityMetric?.velocity ?? 0;

  // Direction based on actual velocity (day-to-day change)
  const isRising = velocity > 0.5;
  const isFalling = velocity < -0.5;

  // Semantic: for fears/frustrations, falling is good; for optimism, rising is good
  const isGoodDirection = categoryKey === "optimism" ? isRising : isFalling;

  return (
    <div
      className={`px-4 py-3 flex items-center gap-3 hover:bg-white/[0.02] transition-colors ${
        highlight === "rising"
          ? "bg-emerald-500/[0.03]"
          : highlight === "falling"
          ? "bg-red-500/[0.03]"
          : ""
      }`}
    >
      {/* Category Name */}
      <div className="w-24 sm:w-28">
        <div className="flex items-center gap-2">
          <span className="text-sm text-white/80">{label}</span>
          {highlight && (
            <span className={`text-[9px] ${highlight === "rising" ? "text-emerald-400" : "text-red-400"}`}>
              {highlight === "rising" ? "▲" : "▼"}
            </span>
          )}
        </div>
        <p className="text-[9px] text-white/30 mt-0.5">{count} quotes {isDaily ? "today" : "this week"}</p>
      </div>

      <DivergingBar
        value={velocityZscore}
        maxValue={3}
        isPositive={velocityZscore >= 0}
        color={isGoodDirection ? "emerald" : "red"}
        formatValue={(v) => `${v >= 0 ? "+" : ""}${v.toFixed(1)}`}
      />
    </div>
  );
}
