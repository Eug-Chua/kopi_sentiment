"use client";

import { DailySentimentScore } from "@/types";

interface CategoryHeatmapProps {
  dataPoints: DailySentimentScore[];
}

type CategoryKey = "fears" | "frustrations" | "optimism";

interface CategoryConfig {
  key: CategoryKey;
  label: string;
  shortLabel: string;
  zscoreField: keyof DailySentimentScore;
  countField: keyof DailySentimentScore;
}

const CATEGORIES: CategoryConfig[] = [
  { key: "fears", label: "Fears", shortLabel: "FRS", zscoreField: "fears_zscore_sum", countField: "fears_count" },
  { key: "frustrations", label: "Frustrations", shortLabel: "FRT", zscoreField: "frustrations_zscore_sum", countField: "frustrations_count" },
  { key: "optimism", label: "Optimism", shortLabel: "OPT", zscoreField: "optimism_zscore_sum", countField: "optimism_count" },
];

/**
 * Category heatmap showing daily z-score intensity by category.
 * Color intensity indicates strength of each category per day.
 */
export function CategoryHeatmap({ dataPoints }: CategoryHeatmapProps) {
  // Calculate max absolute z-score for normalization
  const allZScores = dataPoints.flatMap(dp =>
    CATEGORIES.map(cat => Math.abs(dp[cat.zscoreField] as number))
  );
  const maxAbsZScore = Math.max(...allZScores, 1);

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div>
              <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
                Category Heatmap
              </p>
              <p className="text-xs text-white/30 mt-0.5">Brighter = stronger sentiment that day</p>
            </div>
            {/* Z-score info tooltip */}
            <div className="relative group">
              <button className="w-4 h-4 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-[10px] text-white/40 hover:text-white/60 transition-colors">
                ?
              </button>
              <div className="absolute left-0 top-full mt-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30">
                <div className="bg-[#18181b] border border-white/10 rounded-lg px-3 py-2.5 shadow-xl shadow-black/50 w-64">
                  <p className="text-[10px] font-medium text-white/70 mb-1.5">How to read this</p>
                  <div className="text-[9px] text-white/50 space-y-1">
                    <p>Each cell shows one day&apos;s sentiment strength for that category.</p>
                    <p className="mt-1.5"><span className="text-white/70">Brighter color</span> = more intense/engaged discussion</p>
                    <p><span className="text-white/70">Darker color</span> = quieter day for that emotion</p>
                    <p className="text-white/30 mt-2">Hover over any cell for details.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-[9px]">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-amber-500/50" />
              <span className="text-amber-400">Fears</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-red-500/50" />
              <span className="text-red-400">Frust</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-sm bg-emerald-500/50" />
              <span className="text-emerald-400">Optim</span>
            </div>
          </div>
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="p-4">
        {/* Date headers */}
        <div className="flex mb-2">
          <div className="w-20 shrink-0" /> {/* Spacer for row labels */}
          <div className="flex-1 flex gap-[2px]">
            {dataPoints.map((dp, i) => (
              <div
                key={dp.date}
                className="flex-1 text-center text-[9px] text-white/30 tabular-nums"
              >
                {i === 0 || i === dataPoints.length - 1 ? formatDateShort(dp.date) : ""}
              </div>
            ))}
          </div>
        </div>

        {/* Category rows */}
        <div className="space-y-[2px]">
          {CATEGORIES.map((cat) => (
            <HeatmapRow
              key={cat.key}
              category={cat}
              dataPoints={dataPoints}
              maxAbsZScore={maxAbsZScore}
            />
          ))}
        </div>

        {/* Summary row - total activity */}
        <div className="flex mt-3 pt-3 border-t border-white/[0.04]">
          <div className="w-20 shrink-0 flex items-center">
            <span className="text-[10px] text-white/40">Total</span>
          </div>
          <div className="flex-1 flex gap-[2px]">
            {dataPoints.map((dp) => {
              const total = dp.total_quotes;
              const maxTotal = Math.max(...dataPoints.map(d => d.total_quotes));
              const intensity = total / maxTotal;

              return (
                <div
                  key={`total-${dp.date}`}
                  className="flex-1 h-4 rounded-sm relative group cursor-crosshair"
                  style={{
                    backgroundColor: `rgba(255, 255, 255, ${0.05 + intensity * 0.2})`,
                  }}
                >
                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                    <div className="bg-[#18181b] border border-white/10 rounded px-2 py-1 shadow-xl whitespace-nowrap">
                      <p className="text-[9px] text-white/40">{formatDate(dp.date)}</p>
                      <p className="text-[10px] text-white/70 tabular-nums">{total} quotes</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

interface HeatmapRowProps {
  category: CategoryConfig;
  dataPoints: DailySentimentScore[];
  maxAbsZScore: number;
}

// Category-specific colors
const categoryColorMap: Record<CategoryKey, { r: number; g: number; b: number; textClass: string }> = {
  fears: { r: 245, g: 158, b: 11, textClass: "text-amber-400" },        // amber
  frustrations: { r: 239, g: 68, b: 68, textClass: "text-red-400" },    // red
  optimism: { r: 16, g: 185, b: 129, textClass: "text-emerald-400" },   // emerald
};

function HeatmapRow({ category, dataPoints, maxAbsZScore }: HeatmapRowProps) {
  const color = categoryColorMap[category.key];

  return (
    <div className="flex">
      {/* Row label */}
      <div className="w-20 shrink-0 flex items-center gap-2">
        <span className={`text-[9px] font-mono bg-white/5 px-1.5 py-0.5 rounded ${color.textClass}`}>
          {category.shortLabel}
        </span>
      </div>

      {/* Cells */}
      <div className="flex-1 flex gap-[2px]">
        {dataPoints.map((dp, index) => {
          const zscore = (dp[category.zscoreField] as number) ?? 0;
          const quoteCount = (dp[category.countField] as number) ?? 0;
          const normalizedIntensity = Math.abs(zscore) / maxAbsZScore;

          // Calculate change from previous day
          const prevZscore = index > 0 ? (dataPoints[index - 1][category.zscoreField] as number) ?? 0 : zscore;
          const zscoreChange = zscore - prevZscore;
          const hasChange = index > 0;

          // Format z-score for display in cell
          const displayZ = zscore.toFixed(0);

          return (
            <div
              key={`${category.key}-${dp.date}`}
              className="flex-1 h-8 rounded-sm relative group cursor-crosshair transition-all hover:ring-1 hover:ring-white/20 flex items-center justify-center"
              style={{
                backgroundColor: `rgba(${color.r}, ${color.g}, ${color.b}, ${0.15 + normalizedIntensity * 0.5})`,
              }}
            >
              {/* Z-score in cell */}
              <span className={`text-[9px] font-medium tabular-nums ${
                normalizedIntensity > 0.5 ? "text-white/90" : "text-white/50"
              }`}>
                {displayZ}
              </span>

              {/* Enhanced Tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                <div className="bg-[#18181b] border border-white/10 rounded-lg px-2.5 py-2 shadow-xl shadow-black/50 whitespace-nowrap">
                  <p className="text-[9px] text-white/40 mb-1">{formatDate(dp.date)}</p>
                  <p className={`text-[11px] font-medium ${color.textClass}`}>{category.label}</p>

                  {/* Z-score with change */}
                  <div className="flex items-center gap-1.5 mt-1">
                    <span className={`text-[11px] font-medium tabular-nums ${color.textClass}`}>
                      z = {zscore >= 0 ? "+" : ""}{zscore.toFixed(1)}
                    </span>
                    {hasChange && (
                      <span className={`text-[9px] tabular-nums ${
                        zscoreChange > 0 ? "text-white/50" : zscoreChange < 0 ? "text-white/50" : "text-white/30"
                      }`}>
                        ({zscoreChange >= 0 ? "+" : ""}{zscoreChange.toFixed(1)})
                      </span>
                    )}
                  </div>

                  {/* Quote count */}
                  <p className="text-[10px] text-white/50 mt-1 pt-1 border-t border-white/10">
                    {quoteCount} {quoteCount === 1 ? "quote" : "quotes"}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function formatDateShort(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}