"use client";

import { DailySentimentScore } from "@/types";

interface SentimentCompositionProps {
  dataPoints: DailySentimentScore[];
  isDaily?: boolean;
}

interface BreadthData {
  label: string;
  fears: number;
  frustrations: number;
  optimism: number;
  positive: number;
  negative: number;
  total: number;
  breadthRatio: number;
  fearsPercent: number;
  frustPercent: number;
  optimPercent: number;
}

/**
 * Sentiment composition showing all 3 categories: fears, frustrations, and optimism.
 * Daily mode: Shows daily breakdown with dates
 * Weekly mode: Aggregates data by week to show week-over-week comparison
 */
export function SentimentComposition({ dataPoints, isDaily }: SentimentCompositionProps) {
  // For daily mode, show each day individually
  // For weekly mode, group data by week to show week-over-week comparison
  const breadthData: BreadthData[] = isDaily
    ? dataPoints.map((dp) => computeBreadth(dp, formatDateShort(dp.date)))
    : aggregateByWeeks(dataPoints);

  // Current stats (last item)
  const current = breadthData[breadthData.length - 1];

  // For daily mode, compare to previous day; for weekly, no comparison available
  const previous = breadthData.length > 1 ? breadthData[breadthData.length - 2] : null;
  const breadthChange = previous ? current.breadthRatio - previous.breadthRatio : null;

  // Average breadth (only meaningful for daily with multiple days)
  const avgBreadth = breadthData.length > 1
    ? breadthData.reduce((sum, d) => sum + d.breadthRatio, 0) / breadthData.length
    : current.breadthRatio;
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
            <p className="text-xs text-white/30 mt-0.5">
              {isDaily ? "Daily breakdown" : "Week-over-week"}
            </p>
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
              {breadthChange !== null && (
                <span className={`text-xs ${breadthChange >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {breadthChange >= 0 ? "▲" : "▼"} {Math.abs(breadthChange * 100).toFixed(1)}%
                </span>
              )}
            </div>
            {isDaily && breadthData.length > 1 && (
              <p className="text-[10px] text-white/40 mt-1">
                {isAboveAvg ? "Above" : "Below"} {(avgBreadth * 100).toFixed(1)}% avg
              </p>
            )}
            {!isDaily && (
              <p className="text-[10px] text-white/40 mt-1">
                {current.total} quotes ({current.label})
              </p>
            )}
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

        {/* Stacked bar chart */}
        <div className="space-y-1">
          {breadthData.map((data, i) => {
            const isLast = i === breadthData.length - 1;

            return (
              <div key={data.label} className="flex items-center gap-2 group">
                <span className={`w-10 text-[9px] tabular-nums ${
                  isLast ? "text-white/60" : "text-white/30"
                }`}>
                  {data.label}
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

function computeBreadth(dp: DailySentimentScore, label: string): BreadthData {
  const fears = dp.fears_count;
  const frustrations = dp.frustrations_count;
  const optimism = dp.optimism_count;
  const positive = optimism;
  const negative = fears + frustrations;
  const total = fears + frustrations + optimism;
  const breadthRatio = total > 0 ? (positive - negative) / total : 0;

  return {
    label,
    fears,
    frustrations,
    optimism,
    positive,
    negative,
    total,
    breadthRatio,
    fearsPercent: total > 0 ? (fears / total) * 100 : 0,
    frustPercent: total > 0 ? (frustrations / total) * 100 : 0,
    optimPercent: total > 0 ? (optimism / total) * 100 : 0,
  };
}

function aggregateByWeeks(dataPoints: DailySentimentScore[]): BreadthData[] {
  // Group data points by ISO week
  const weekMap = new Map<string, DailySentimentScore[]>();

  for (const dp of dataPoints) {
    const weekLabel = getWeekLabel(dp.date);
    if (!weekMap.has(weekLabel)) {
      weekMap.set(weekLabel, []);
    }
    weekMap.get(weekLabel)!.push(dp);
  }

  // Convert to sorted array of week aggregates
  const sortedEntries = Array.from(weekMap.entries())
    .sort((a, b) => a[0].localeCompare(b[0])); // Sort by week label (W03, W04, W05)

  const weeks = sortedEntries.map(([weekLabel, points], index) => {
      const totals = points.reduce(
        (acc, dp) => ({
          fears: acc.fears + dp.fears_count,
          frustrations: acc.frustrations + dp.frustrations_count,
          optimism: acc.optimism + dp.optimism_count,
        }),
        { fears: 0, frustrations: 0, optimism: 0 }
      );

      const positive = totals.optimism;
      const negative = totals.fears + totals.frustrations;
      const total = totals.fears + totals.frustrations + totals.optimism;
      const breadthRatio = total > 0 ? (positive - negative) / total : 0;

      // Label the last week as "Current" instead of week number
      const isLastWeek = index === sortedEntries.length - 1;
      const displayLabel = isLastWeek ? "Current" : weekLabel;

      return {
        label: displayLabel,
        fears: totals.fears,
        frustrations: totals.frustrations,
        optimism: totals.optimism,
        positive,
        negative,
        total,
        breadthRatio,
        fearsPercent: total > 0 ? (totals.fears / total) * 100 : 0,
        frustPercent: total > 0 ? (totals.frustrations / total) * 100 : 0,
        optimPercent: total > 0 ? (totals.optimism / total) * 100 : 0,
      };
    });

  return weeks.length > 0 ? weeks : [{
    label: "N/A",
    fears: 0,
    frustrations: 0,
    optimism: 0,
    positive: 0,
    negative: 0,
    total: 0,
    breadthRatio: 0,
    fearsPercent: 0,
    frustPercent: 0,
    optimPercent: 0,
  }];
}

function getWeekLabel(dateStr: string): string {
  const [year, month, day] = dateStr.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));

  // ISO 8601 week calculation
  // Week 1 is the week containing Jan 4th (or equivalently, the week with the first Thursday)
  const dayOfWeek = date.getUTCDay() || 7; // Make Sunday = 7

  // Set to nearest Thursday (current date + 4 - day of week)
  const thursday = new Date(date);
  thursday.setUTCDate(date.getUTCDate() + 4 - dayOfWeek);

  // Get first day of year for the Thursday's year
  const yearStart = new Date(Date.UTC(thursday.getUTCFullYear(), 0, 1));

  // Calculate week number
  const weekNumber = Math.ceil((((thursday.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);

  return `W${String(weekNumber).padStart(2, "0")}`;
}

function formatDateShort(dateStr: string): string {
  const [, month, day] = dateStr.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${day}${months[parseInt(month) - 1]}`;
}
