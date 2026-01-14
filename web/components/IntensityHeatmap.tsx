"use client";

import { OverallSentiment, Intensity } from "@/types";

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

interface IntensityHeatmapProps {
  sentiment: OverallSentiment;
  onCellClick?: (category: CategoryKey, intensity: Intensity) => void;
}

function getHeatColor(value: number, max: number, level: Intensity): string {
  if (value === 0) return "bg-zinc-800/50";

  const intensity = max > 0 ? value / max : 0;

  // Base colors by intensity level
  if (level === "mild") {
    // Light grey gradient
    if (intensity < 0.33) return "bg-zinc-600/30";
    if (intensity < 0.66) return "bg-zinc-500/50";
    return "bg-zinc-400/70";
  }

  if (level === "moderate") {
    // Amber gradient
    if (intensity < 0.33) return "bg-amber-700/30";
    if (intensity < 0.66) return "bg-amber-600/50";
    return "bg-amber-500/70";
  }

  // Strong - Red gradient
  if (intensity < 0.33) return "bg-red-700/30";
  if (intensity < 0.66) return "bg-red-600/50";
  return "bg-red-500/70";
}

function HeatCell({
  value,
  max,
  level,
  onClick,
}: {
  value: number;
  max: number;
  level: Intensity;
  onClick?: () => void;
}) {
  const textColor = value === 0 ? "text-zinc-600" : "text-white";
  const isClickable = onClick && value > 0;

  return (
    <div
      onClick={isClickable ? onClick : undefined}
      className={`w-full h-12 rounded flex items-center justify-center text-sm font-medium transition-colors ${getHeatColor(value, max, level)} ${textColor} ${isClickable ? "cursor-pointer hover:ring-2 hover:ring-white/30" : ""}`}
    >
      {value}
    </div>
  );
}

export function IntensityHeatmap({ sentiment, onCellClick }: IntensityHeatmapProps) {
  const categories: { key: CategoryKey; label: string; data: typeof sentiment.fears }[] = [
    { key: "fears", label: "Fears", data: sentiment.fears },
    { key: "frustrations", label: "Frustrations", data: sentiment.frustrations },
    { key: "goals", label: "Goals", data: sentiment.goals },
    { key: "aspirations", label: "Aspirations", data: sentiment.aspirations },
  ];

  // Find max value per column for color scaling
  const maxMild = Math.max(...categories.map((c) => c.data.intensity_breakdown.mild), 1);
  const maxModerate = Math.max(...categories.map((c) => c.data.intensity_breakdown.moderate), 1);
  const maxStrong = Math.max(...categories.map((c) => c.data.intensity_breakdown.strong), 1);

  // Calculate totals
  const categoryStats = categories.map((cat) => {
    const { mild, moderate, strong } = cat.data.intensity_breakdown;
    const total = mild + moderate + strong;
    return { ...cat, total };
  });

  const handleCellClick = (category: CategoryKey, intensity: Intensity) => {
    if (onCellClick) {
      onCellClick(category, intensity);
    }
  };

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800">
      {/* Header */}
      <div className="grid grid-cols-[120px_1fr_1fr_1fr_60px] gap-2 mb-2">
        <div className="text-xs text-muted-foreground"></div>
        <div className="text-xs text-muted-foreground text-center">Mild</div>
        <div className="text-xs text-muted-foreground text-center">Moderate</div>
        <div className="text-xs text-muted-foreground text-center">Strong</div>
        <div className="text-xs text-muted-foreground text-center">Total</div>
      </div>

      {/* Rows */}
      {categoryStats.map((cat) => (
        <div key={cat.key} className="grid grid-cols-[120px_1fr_1fr_1fr_60px] gap-2 mb-2">
          <div className="flex items-center text-sm text-white font-medium">
            {cat.label}
          </div>
          <HeatCell
            value={cat.data.intensity_breakdown.mild}
            max={maxMild}
            level="mild"
            onClick={() => handleCellClick(cat.key, "mild")}
          />
          <HeatCell
            value={cat.data.intensity_breakdown.moderate}
            max={maxModerate}
            level="moderate"
            onClick={() => handleCellClick(cat.key, "moderate")}
          />
          <HeatCell
            value={cat.data.intensity_breakdown.strong}
            max={maxStrong}
            level="strong"
            onClick={() => handleCellClick(cat.key, "strong")}
          />
          <div className="flex items-center justify-center text-sm text-zinc-400 bg-zinc-800/50 rounded h-12">
            {cat.total}
          </div>
        </div>
      ))}

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-zinc-800 flex items-center gap-4 text-xs text-muted-foreground">
        <span>Color by intensity:</span>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-zinc-400/70"></div>
          <span>Mild</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-amber-500/70"></div>
          <span>Moderate</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded bg-red-500/70"></div>
          <span>Strong</span>
        </div>
      </div>
    </div>
  );
}