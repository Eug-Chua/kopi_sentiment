"use client";

import { MomentumReport, CategoryMomentum, VelocityReport, VelocityMetric } from "@/types";

interface MomentumDisplayProps {
  momentum: MomentumReport;
  velocity?: VelocityReport;
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
export function MomentumDisplay({ momentum, velocity }: MomentumDisplayProps) {
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

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Category Velocity
            </p>
            <p className="text-xs text-white/30 mt-0.5">Today's change vs historical</p>
          </div>
          {/* Legend for z-score interpretation */}
          <div className="flex items-center gap-2 text-[9px] text-white/40">
            <span className="text-white/50">|σ|:</span>
            <span className="text-white/50">&lt;1 normal</span>
            <span className="text-amber-400">1-2 notable</span>
            <span className="text-red-400">&gt;2 unusual</span>
          </div>
        </div>
      </div>

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
          Velocity σ shows how unusual today's change is. |σ| &gt; 2 = statistically significant.
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
}

function MomentumRow({ label, categoryKey, data, velocityMetric, highlight }: MomentumRowProps) {
  // Handle missing data gracefully
  if (!data) {
    return (
      <div className="px-4 py-3 flex items-center gap-4 text-white/30 text-xs">
        <span className="text-xs">{label}</span>
        <span>No data available</span>
      </div>
    );
  }

  const zscore = data.current_zscore_sum ?? 0;
  const count = data.current_count ?? 0;

  // Get velocity data if available
  const velocityZscore = velocityMetric?.velocity_zscore ?? 0;
  const velocity = velocityMetric?.velocity ?? 0;

  // Direction based on actual velocity (day-to-day change)
  const isRising = velocity > 0.5;
  const isFalling = velocity < -0.5;

  // Color based on velocity z-score magnitude (how unusual)
  // AND semantic meaning (for fears/frustrations: rising = bad, for optimism: rising = good)
  const absVelZ = Math.abs(velocityZscore);
  const isUnusual = absVelZ >= 2.0;
  const isNotable = absVelZ >= 1.0;

  // Semantic: for fears/frustrations, falling is good; for optimism, rising is good
  const isGoodDirection = categoryKey === "optimism" ? isRising : isFalling;

  // Color the z-score based on unusualness and direction
  let zscoreColor = "text-white/50"; // Normal
  if (isUnusual) {
    zscoreColor = isGoodDirection ? "text-emerald-400" : "text-red-400";
  } else if (isNotable) {
    zscoreColor = isGoodDirection ? "text-emerald-400/70" : "text-amber-400";
  }

  // Arrow color based on direction and category
  const arrowColor = isGoodDirection ? "text-emerald-400" : (isRising || isFalling) ? "text-red-400" : "text-white/40";

  // Z-score bar visualization (normalized to reasonable range)
  const maxZscore = 150; // Cap for visualization
  const normalizedZ = Math.min(Math.abs(zscore), maxZscore);
  const barWidth = (normalizedZ / maxZscore) * 100;

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
        <p className="text-[9px] text-white/30 mt-0.5">{count} quotes today</p>
      </div>

      {/* Z-score bar (intensity level) */}
      <div className="flex-1">
        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              categoryKey === "optimism" ? "bg-emerald-500/60" : "bg-amber-500/60"
            }`}
            style={{ width: `${barWidth}%` }}
          />
        </div>
        <p className="text-[9px] text-white/30 mt-0.5">
          Intensity: {Math.abs(zscore).toFixed(0)}
        </p>
      </div>

      {/* Velocity Z-score indicator */}
      <div className="text-right w-16">
        <p className={`text-sm font-medium tabular-nums ${zscoreColor}`}>
          {velocityZscore >= 0 ? "+" : ""}{velocityZscore.toFixed(1)}σ
        </p>
        <p className="text-[8px] text-white/30 mt-0.5">
          velocity
        </p>
      </div>

      {/* Direction arrow */}
      <div className={`w-6 text-center text-lg ${arrowColor}`}>
        {isRising ? "↗" : isFalling ? "↘" : "→"}
      </div>
    </div>
  );
}
