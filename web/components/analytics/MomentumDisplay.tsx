"use client";

import { useState } from "react";
import { MomentumReport, CategoryMomentum } from "@/types";

interface MomentumDisplayProps {
  momentum: MomentumReport;
}

type Period = "1D" | "3D" | "7D";

/**
 * Category momentum display with trading-app aesthetics.
 * Shows rate of change for each FFO category like a stock watchlist.
 */
export function MomentumDisplay({ momentum }: MomentumDisplayProps) {
  const [selectedPeriod, setSelectedPeriod] = useState<Period>("7D");

  const categories: {
    key: keyof Pick<MomentumReport, "fears" | "frustrations" | "optimism">;
    label: string;
  }[] = [
    { key: "fears", label: "Fears" },
    { key: "frustrations", label: "Frustrations" },
    { key: "optimism", label: "Optimism" },
  ];

  const periodLabels: Record<Period, string> = {
    "1D": "1-day",
    "3D": "3-day",
    "7D": "7-day",
  };

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Category Momentum
            </p>
            <p className="text-xs text-white/30 mt-0.5">{periodLabels[selectedPeriod]} intensity change</p>
          </div>
          <div className="flex gap-1">
            {(["1D", "3D", "7D"] as Period[]).map((period) => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period)}
                className={`px-2 py-0.5 rounded text-[10px] transition-colors ${
                  selectedPeriod === period
                    ? "bg-white/10 text-white/80"
                    : "text-white/30 hover:text-white/50 hover:bg-white/5"
                }`}
              >
                {period}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Watchlist-style rows */}
      <div className="divide-y divide-white/[0.04]">
        {categories.map(({ key, label }) => {
          const cat = momentum[key] as CategoryMomentum;
          const isFastestRising = momentum.fastest_rising === key;
          const isFastestFalling = momentum.fastest_falling === key;

          return (
            <MomentumRow
              key={key}
              label={label}
              categoryKey={key}
              data={cat}
              selectedPeriod={selectedPeriod}
              highlight={isFastestRising ? "rising" : isFastestFalling ? "falling" : null}
            />
          );
        })}
      </div>

      {/* Footer summary */}
      <div className="p-3 border-t border-white/[0.04]">
        <div className="flex items-center justify-between text-[10px]">
          <div className="flex items-center gap-4">
            <span className="text-white/30">Most active:</span>
            <span className="text-emerald-400">
              ↑ {momentum.fastest_rising.charAt(0).toUpperCase() + momentum.fastest_rising.slice(1)}
            </span>
            <span className="text-red-400">
              ↓ {momentum.fastest_falling.charAt(0).toUpperCase() + momentum.fastest_falling.slice(1)}
            </span>
          </div>
        </div>
        <p className="text-[9px] text-white/30 mt-2">
          Shows how much each emotion&apos;s intensity has changed. ↑ = emotion growing stronger.
        </p>
      </div>
    </div>
  );
}

interface MomentumRowProps {
  label: string;
  categoryKey: "fears" | "frustrations" | "optimism";
  data: CategoryMomentum;
  selectedPeriod: Period;
  highlight: "rising" | "falling" | null;
}

function MomentumRow({ label, categoryKey, data, selectedPeriod, highlight }: MomentumRowProps) {
  // Handle missing data gracefully
  if (!data) {
    return (
      <div className="px-4 py-3 flex items-center gap-4 text-white/30 text-xs">
        <span className="text-xs">{label}</span>
        <span>No data available</span>
      </div>
    );
  }

  // Get the ROC value based on selected period
  const rocValue = selectedPeriod === "1D" ? (data.roc_1d ?? 0) : selectedPeriod === "3D" ? (data.roc_3d ?? 0) : (data.roc_7d ?? 0);

  // Semantic color coding: green = good for sentiment, red = bad
  // For fears/frustrations: rising = bad (red), falling = good (green)
  // For optimism: rising = good (green), falling = bad (red)
  const isGoodChange = categoryKey === "optimism" ? rocValue >= 0 : rocValue <= 0;
  const changeColor = isGoodChange ? "text-emerald-400" : "text-red-400";

  // Sparkline-style mini bars for 1d, 3d, 7d
  const periods = [
    { label: "1D", value: data.roc_1d ?? 0, selected: selectedPeriod === "1D" },
    { label: "3D", value: data.roc_3d ?? 0, selected: selectedPeriod === "3D" },
    { label: "7D", value: data.roc_7d ?? 0, selected: selectedPeriod === "7D" },
  ];
  const maxAbs = Math.max(...periods.map((p) => Math.abs(p.value)), 1);

  return (
    <div
      className={`px-4 py-3 flex items-center gap-4 hover:bg-white/[0.02] transition-colors ${
        highlight === "rising"
          ? "bg-emerald-500/[0.03]"
          : highlight === "falling"
          ? "bg-red-500/[0.03]"
          : ""
      }`}
    >
      {/* Category Name */}
      <div className="w-28">
        <div className="flex items-center gap-2">
          <span className="text-sm text-white/80">{label}</span>
          {highlight && (
            <span className={`text-[9px] ${highlight === "rising" ? "text-emerald-400" : "text-red-400"}`}>
              {highlight === "rising" ? "▲" : "▼"}
            </span>
          )}
        </div>
      </div>

      {/* Mini period bars */}
      <div className="flex-1 flex items-center gap-1">
        {periods.map((period) => {
          const width = (Math.abs(period.value) / maxAbs) * 100;
          // Semantic coloring: green = good, red = bad
          const isGood = categoryKey === "optimism" ? period.value >= 0 : period.value <= 0;
          return (
            <div key={period.label} className="flex-1">
              <div className={`h-1.5 bg-white/5 rounded-full overflow-hidden ${period.selected ? "ring-1 ring-white/20" : ""}`}>
                <div
                  className={`h-full rounded-full transition-all ${
                    isGood ? "bg-emerald-500/50" : "bg-red-500/50"
                  } ${period.selected ? (isGood ? "bg-emerald-500/80" : "bg-red-500/80") : ""}`}
                  style={{ width: `${Math.min(width, 100)}%` }}
                />
              </div>
              <p className={`text-[9px] text-center mt-0.5 ${period.selected ? "text-white/60" : "text-white/30"}`}>
                {period.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Main change value */}
      <div className="text-right w-20">
        <p className={`text-sm font-medium tabular-nums ${changeColor}`}>
          {rocValue >= 0 ? "+" : ""}{rocValue.toFixed(1)}%
        </p>
        <div className="flex items-center justify-end gap-1 mt-0.5">
          <TrendStrengthDots strength={data.trend_strength ?? "weak"} />
          <span className="text-[9px] text-white/30 capitalize">{data.trend_strength ?? "weak"}</span>
        </div>
      </div>

      {/* Trend arrow */}
      <div className={`w-8 text-center text-lg ${changeColor}`}>
        {data.trend === "rising" ? "↗" : data.trend === "falling" ? "↘" : "→"}
      </div>
    </div>
  );
}

function TrendStrengthDots({ strength }: { strength: string }) {
  const count = strength === "strong" ? 3 : strength === "moderate" ? 2 : 1;
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`w-1 h-1 rounded-full ${
            i <= count ? "bg-white/60" : "bg-white/10"
          }`}
        />
      ))}
    </div>
  );
}