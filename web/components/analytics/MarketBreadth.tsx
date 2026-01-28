"use client";

import { DailySentimentScore } from "@/types";

interface SentimentCompositionProps {
  dataPoints: DailySentimentScore[];
}

/**
 * Sentiment composition showing all 3 categories: fears, frustrations, and optimism.
 * Shows the daily spread and percentage breakdown with 3-segment stacked bars.
 */
export function SentimentComposition({ dataPoints }: SentimentCompositionProps) {
  // Calculate breadth for each day
  const breadthData = dataPoints.map((dp) => {
    const fears = dp.fears_count;
    const frustrations = dp.frustrations_count;
    const optimism = dp.optimism_count;
    const positive = optimism;
    const negative = fears + frustrations;
    const total = fears + frustrations + optimism;
    const breadthRatio = total > 0 ? (positive - negative) / total : 0;
    const positivePercent = total > 0 ? (positive / total) * 100 : 50;

    return {
      date: dp.date,
      fears,
      frustrations,
      optimism,
      positive,
      negative,
      total,
      breadthRatio,
      positivePercent,
      fearsPercent: total > 0 ? (fears / total) * 100 : 0,
      frustPercent: total > 0 ? (frustrations / total) * 100 : 0,
      optimPercent: total > 0 ? (optimism / total) * 100 : 0,
    };
  });

  // Current stats
  const current = breadthData[breadthData.length - 1];
  const previous = breadthData.length > 1 ? breadthData[breadthData.length - 2] : current;
  const breadthChange = current.breadthRatio - previous.breadthRatio;

  // Average breadth
  const avgBreadth = breadthData.reduce((sum, d) => sum + d.breadthRatio, 0) / breadthData.length;
  const isAboveAvg = current.breadthRatio > avgBreadth;

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Sentiment Composition
            </p>
            <p className="text-xs text-white/30 mt-0.5">Category breakdown over time</p>
          </div>
          <div className={`px-2.5 py-1 rounded-md text-xs font-medium ${
            current.breadthRatio > 0
              ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
              : current.breadthRatio < 0
              ? "bg-red-500/10 text-red-400 border border-red-500/20"
              : "bg-white/5 text-white/60 border border-white/10"
          }`}>
            {current.breadthRatio > 0 ? "Bullish" : current.breadthRatio < 0 ? "Bearish" : "Neutral"}
          </div>
        </div>
      </div>

      <div className="p-4">
        {/* Current breadth display */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-light tabular-nums ${
                current.breadthRatio >= 0 ? "text-emerald-400" : "text-red-400"
              }`}>
                {current.breadthRatio >= 0 ? "+" : ""}{(current.breadthRatio * 100).toFixed(1)}%
              </span>
              <span className={`text-xs ${breadthChange >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {breadthChange >= 0 ? "▲" : "▼"} {Math.abs(breadthChange * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-[10px] text-white/40 mt-1">
              {isAboveAvg ? "Above" : "Below"} {(avgBreadth * 100).toFixed(1)}% avg
            </p>
          </div>

          {/* Category percentages */}
          <div className="flex gap-3 text-center">
            <div>
              <p className="text-[10px] text-amber-400">Fears</p>
              <p className="text-sm font-medium text-amber-400 tabular-nums">{current.fearsPercent.toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-[10px] text-red-400">Frust.</p>
              <p className="text-sm font-medium text-red-400 tabular-nums">{current.frustPercent.toFixed(0)}%</p>
            </div>
            <div>
              <p className="text-[10px] text-emerald-400">Optim.</p>
              <p className="text-sm font-medium text-emerald-400 tabular-nums">{current.optimPercent.toFixed(0)}%</p>
            </div>
          </div>
        </div>

        {/* Stacked bar chart showing breadth over time */}
        <div className="space-y-1">
          {breadthData.map((data, i) => {
            const isLast = i === breadthData.length - 1;

            return (
              <div key={data.date} className="flex items-center gap-2 group">
                <span className={`w-10 text-[9px] tabular-nums ${
                  isLast ? "text-white/60" : "text-white/30"
                }`}>
                  {formatDateShort(data.date)}
                </span>

                {/* Stacked bar - 3 segments: fears, frustrations, optimism */}
                <div className={`flex-1 h-4 flex rounded-sm overflow-hidden ${
                  isLast ? "ring-1 ring-white/20" : ""
                }`}>
                  <div
                    className="bg-amber-500/50 transition-all group-hover:bg-amber-500/70"
                    style={{ width: `${data.fearsPercent}%` }}
                    title={`Fears: ${data.fears}`}
                  />
                  <div
                    className="bg-red-500/50 transition-all group-hover:bg-red-500/70"
                    style={{ width: `${data.frustPercent}%` }}
                    title={`Frustrations: ${data.frustrations}`}
                  />
                  <div
                    className="bg-emerald-500/50 transition-all group-hover:bg-emerald-500/70"
                    style={{ width: `${data.optimPercent}%` }}
                    title={`Optimism: ${data.optimism}`}
                  />
                </div>

                <span
                  className={`w-12 text-[9px] tabular-nums text-right ${
                    data.breadthRatio >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                  title={`${data.positive} positive vs ${data.negative} negative (${data.total} total)`}
                >
                  {data.breadthRatio >= 0 ? "+" : ""}{(data.breadthRatio * 100).toFixed(0)}%
                </span>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="mt-4 pt-3 border-t border-white/[0.04] flex items-center justify-between text-[10px]">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm bg-amber-500/50" />
              <span className="text-white/40">Fears</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm bg-red-500/50" />
              <span className="text-white/40">Frustrations</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-sm bg-emerald-500/50" />
              <span className="text-white/40">Optimism</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function formatDateShort(dateStr: string): string {
  // Parse date string directly to avoid timezone issues
  const [, month, day] = dateStr.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${day}${months[parseInt(month) - 1]}`;
}