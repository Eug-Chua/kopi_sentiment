"use client";

import { OverallSentiment, Intensity } from "@/types";

type CategoryKey = "fears" | "frustrations" | "optimism";

interface IntensityHeatmapProps {
  sentiment: OverallSentiment;
  onCellClick?: (category: CategoryKey, intensity?: Intensity) => void;
  className?: string;
}

function getHeatColor(value: number, max: number, level: Intensity, category: CategoryKey): string {
  if (value === 0) return "bg-white/[0.03]";

  const intensity = max > 0 ? value / max : 0;

  // Optimism uses green gradients (positive emotion)
  if (category === "optimism") {
    if (level === "mild") {
      if (intensity < 0.33) return "bg-emerald-700/30";
      if (intensity < 0.66) return "bg-emerald-600/50";
      return "bg-emerald-500/70";
    }
    if (level === "moderate") {
      if (intensity < 0.33) return "bg-emerald-600/30";
      if (intensity < 0.66) return "bg-emerald-500/50";
      return "bg-emerald-400/70";
    }
    // strong
    if (intensity < 0.33) return "bg-emerald-500/30";
    if (intensity < 0.66) return "bg-emerald-400/50";
    return "bg-emerald-300/70";
  }

  // Fears and Frustrations use gray → amber → red (negative emotions)
  if (level === "mild") {
    if (intensity < 0.33) return "bg-zinc-600/30";
    if (intensity < 0.66) return "bg-zinc-500/50";
    return "bg-zinc-400/70";
  }

  if (level === "moderate") {
    if (intensity < 0.33) return "bg-amber-700/30";
    if (intensity < 0.66) return "bg-amber-600/50";
    return "bg-amber-500/70";
  }

  if (intensity < 0.33) return "bg-red-700/30";
  if (intensity < 0.66) return "bg-red-600/50";
  return "bg-red-500/70";
}

function HeatCell({
  value,
  max,
  level,
  category,
  onClick,
}: {
  value: number;
  max: number;
  level: Intensity;
  category: CategoryKey;
  onClick?: () => void;
}) {
  const textColor = value === 0 ? "text-white/30" : "text-white";
  const isClickable = onClick && value > 0;

  return (
    <div
      onClick={isClickable ? onClick : undefined}
      className={`w-full h-full min-h-8 rounded flex items-center justify-center text-xs font-medium transition-colors ${getHeatColor(value, max, level, category)} ${textColor} ${isClickable ? "cursor-pointer hover:ring-2 hover:ring-white/30" : ""}`}
    >
      {value}
    </div>
  );
}

export function IntensityHeatmap({ sentiment, onCellClick, className }: IntensityHeatmapProps) {
  const categories: { key: CategoryKey; label: string; data: typeof sentiment.fears }[] = [
    { key: "fears", label: "Fears", data: sentiment.fears },
    { key: "frustrations", label: "Frustrations", data: sentiment.frustrations },
    { key: "optimism", label: "Optimism", data: sentiment.optimism },
  ];

  const maxMild = Math.max(...categories.map((c) => c.data.intensity_breakdown.mild), 1);
  const maxModerate = Math.max(...categories.map((c) => c.data.intensity_breakdown.moderate), 1);
  const maxStrong = Math.max(...categories.map((c) => c.data.intensity_breakdown.strong), 1);

  const categoryStats = categories.map((cat) => {
    const { mild, moderate, strong } = cat.data.intensity_breakdown;
    const total = mild + moderate + strong;
    return { ...cat, total };
  });

  const handleCellClick = (category: CategoryKey, intensity?: Intensity) => {
    if (onCellClick) {
      onCellClick(category, intensity);
    }
  };

  return (
    <div className={`bg-black/40 backdrop-blur-sm rounded-xl p-3 border border-white/[0.08] flex flex-col ${className || ""}`}>
      {/* Header */}
      <div className="grid grid-cols-[minmax(70px,1fr)_1fr_1fr_1fr_minmax(35px,0.5fr)] gap-1.5 mb-1.5">
        <div className="text-[10px] text-white/40"></div>
        <div className="text-[10px] text-white/40 text-center">Mild</div>
        <div className="text-[10px] text-white/40 text-center">Moderate</div>
        <div className="text-[10px] text-white/40 text-center">Strong</div>
        <div className="text-[10px] text-white/40 text-center">Total</div>
      </div>

      {/* Rows */}
      <div className="flex-1 flex flex-col gap-1.5">
        {categoryStats.map((cat) => (
          <div key={cat.key} className="grid grid-cols-[minmax(70px,1fr)_1fr_1fr_1fr_minmax(35px,0.5fr)] gap-1.5 flex-1">
            <div className="flex items-center text-xs text-white/80 font-medium">
              {cat.label}
            </div>
            <HeatCell
              value={cat.data.intensity_breakdown.mild}
              max={maxMild}
              level="mild"
              category={cat.key}
              onClick={() => handleCellClick(cat.key, "mild")}
            />
            <HeatCell
              value={cat.data.intensity_breakdown.moderate}
              max={maxModerate}
              level="moderate"
              category={cat.key}
              onClick={() => handleCellClick(cat.key, "moderate")}
            />
            <HeatCell
              value={cat.data.intensity_breakdown.strong}
              max={maxStrong}
              level="strong"
              category={cat.key}
              onClick={() => handleCellClick(cat.key, "strong")}
            />
            <div
              onClick={() => cat.total > 0 && handleCellClick(cat.key)}
              className={`flex items-center justify-center text-xs text-white/50 bg-white/[0.03] rounded h-full min-h-8 ${cat.total > 0 ? "cursor-pointer hover:ring-2 hover:ring-white/30" : ""}`}
            >
              {cat.total}
            </div>
          </div>
        ))}
      </div>

      {/* Legend - more compact */}
      <div className="mt-auto pt-2 border-t border-white/[0.06] flex flex-col gap-1.5 text-[10px] text-white/40">
        <div className="flex items-center gap-3">
          <span className="text-white/50">Negative:</span>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-zinc-400/70"></div>
            <span>Mild</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-amber-500/70"></div>
            <span>Moderate</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-red-500/70"></div>
            <span>Strong</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-white/50">Positive:</span>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-emerald-500/70"></div>
            <span>Mild</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-emerald-400/70"></div>
            <span>Moderate</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2.5 h-2.5 rounded bg-emerald-300/70"></div>
            <span>Strong</span>
          </div>
        </div>
      </div>
    </div>
  );
}