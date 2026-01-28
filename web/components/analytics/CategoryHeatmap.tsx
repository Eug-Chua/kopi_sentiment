"use client";

import { OverallSentiment, Intensity, AllQuotes, QuoteWithMetadata } from "@/types";

interface CategoryHeatmapProps {
  overallSentiment?: OverallSentiment;
  quotes?: AllQuotes;
  /** Compact mode with smaller padding and flexible height */
  compact?: boolean;
}

type CategoryKey = "fears" | "frustrations" | "optimism";

// Category-specific colors
const categoryColors: Record<CategoryKey, { text: string; rgb: string; label: string }> = {
  fears: { text: "text-amber-400", rgb: "245, 158, 11", label: "Fears" },
  frustrations: { text: "text-red-400", rgb: "239, 68, 68", label: "Frustrations" },
  optimism: { text: "text-emerald-400", rgb: "16, 185, 129", label: "Optimism" },
};

// Intensity opacity modifiers
const intensityOpacity: Record<Intensity, number> = {
  mild: 0.5,
  moderate: 0.7,
  strong: 0.9,
};

// Y-axis position for intensity levels
const intensityYPosition: Record<Intensity, number> = {
  mild: 20,
  moderate: 50,
  strong: 80,
};

interface BubbleData {
  category: CategoryKey;
  intensity: Intensity;
  count: number;
  avgEngagement: number;
}

/**
 * Compute bubble data from quotes - groups by category and intensity,
 * calculates count and average engagement for each group.
 */
function computeBubbleData(quotes: AllQuotes): BubbleData[] {
  const categories: CategoryKey[] = ["fears", "frustrations", "optimism"];
  const intensities: Intensity[] = ["mild", "moderate", "strong"];
  const bubbles: BubbleData[] = [];

  for (const category of categories) {
    const categoryQuotes = quotes[category] || [];

    for (const intensity of intensities) {
      const filtered = categoryQuotes.filter((q: QuoteWithMetadata) => q.intensity === intensity);
      if (filtered.length > 0) {
        const totalEngagement = filtered.reduce((sum: number, q: QuoteWithMetadata) =>
          sum + (q.comment_score || 0), 0);
        bubbles.push({
          category,
          intensity,
          count: filtered.length,
          avgEngagement: totalEngagement / filtered.length,
        });
      }
    }
  }

  return bubbles;
}

/**
 * Fallback: compute bubble data from overallSentiment counts only (no engagement data)
 */
function computeBubbleDataFromSentiment(overallSentiment: OverallSentiment): BubbleData[] {
  const categories: CategoryKey[] = ["fears", "frustrations", "optimism"];
  const intensities: Intensity[] = ["mild", "moderate", "strong"];
  const bubbles: BubbleData[] = [];

  for (const category of categories) {
    const breakdown = overallSentiment[category].intensity_breakdown;
    for (const intensity of intensities) {
      const count = breakdown[intensity];
      if (count > 0) {
        bubbles.push({
          category,
          intensity,
          count,
          avgEngagement: 0, // No engagement data available
        });
      }
    }
  }

  return bubbles;
}

/**
 * Scatter bubble chart showing sentiment distribution by category and intensity.
 * X-axis: Average engagement (comment score)
 * Y-axis: Intensity level (mild/moderate/strong)
 * Bubble size: Quote count
 */
export function CategoryHeatmap({ overallSentiment, quotes, compact = false }: CategoryHeatmapProps) {
  if (!overallSentiment && !quotes) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm p-4 h-full">
        <p className="text-white/40 text-sm">No sentiment data available</p>
      </div>
    );
  }

  // Compute bubble data from quotes if available, otherwise from sentiment counts
  const bubbles = quotes
    ? computeBubbleData(quotes)
    : overallSentiment
      ? computeBubbleDataFromSentiment(overallSentiment)
      : [];

  if (bubbles.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm p-4">
        <p className="text-white/40 text-sm">No data to display</p>
      </div>
    );
  }

  // Calculate scales
  const maxEngagement = Math.max(...bubbles.map(b => b.avgEngagement), 1);
  const maxCount = Math.max(...bubbles.map(b => b.count), 1);
  const totalQuotes = bubbles.reduce((sum, b) => sum + b.count, 0);

  // Chart dimensions (percentage-based)
  // In compact mode, add space for axis labels
  const chartLeft = compact ? 12 : 12;
  const chartRight = 96;
  const chartTop = 6;
  const chartBottom = 90;
  const chartWidth = chartRight - chartLeft;
  const chartHeightPercent = chartBottom - chartTop;

  const minChartHeight = compact ? 140 : 200;

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm h-full flex flex-col">
      {/* Header */}
      <div className={`${compact ? "p-3" : "p-4"} border-b border-white/[0.06]`}>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Sentiment Distribution
            </p>
            {!compact && <p className="text-xs text-white/30 mt-0.5">Engagement vs Intensity</p>}
          </div>
          <div className="flex items-center gap-1.5 text-[8px] text-white/30">
            <span className="flex items-center gap-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500/70" />
              <span className="text-amber-400/80">Fear</span>
            </span>
            <span className="flex items-center gap-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500/70" />
              <span className="text-red-400/80">Frust</span>
            </span>
            <span className="flex items-center gap-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/70" />
              <span className="text-emerald-400/80">Optim</span>
            </span>
          </div>
        </div>
      </div>

      {/* Chart container */}
      <div className={`${compact ? "p-2" : "p-4"} flex-1`}>
        <div className="relative w-full h-full" style={{ minHeight: `${minChartHeight}px` }}>
          {/* Y-axis labels - only in non-compact mode */}
          {!compact && (
            <div className="absolute left-0 top-0 bottom-0 w-[10%] flex flex-col justify-between text-[9px] text-white/40 py-2">
              <span className="text-right pr-2">Strong</span>
              <span className="text-right pr-2">Moderate</span>
              <span className="text-right pr-2">Mild</span>
            </div>
          )}

          {/* Chart area with grid */}
          <div
            className="absolute bg-white/[0.02] rounded-lg overflow-hidden"
            style={{
              left: `${chartLeft}%`,
              right: `${100 - chartRight}%`,
              top: `${chartTop}%`,
              bottom: `${100 - chartBottom}%`
            }}
          >
            {/* Horizontal grid lines */}
            <div className="absolute w-full border-t border-white/[0.06]" style={{ top: "33.3%" }} />
            <div className="absolute w-full border-t border-white/[0.06]" style={{ top: "66.6%" }} />

            {/* Vertical grid lines */}
            <div className="absolute h-full border-l border-white/[0.06]" style={{ left: "25%" }} />
            <div className="absolute h-full border-l border-white/[0.06]" style={{ left: "50%" }} />
            <div className="absolute h-full border-l border-white/[0.06]" style={{ left: "75%" }} />
          </div>

          {/* Bubbles */}
          {bubbles.map((bubble) => {
            const colors = categoryColors[bubble.category];
            const opacity = intensityOpacity[bubble.intensity];

            // X position based on engagement (0 to maxEngagement)
            const xPercent = chartLeft + (bubble.avgEngagement / maxEngagement) * chartWidth * 0.9 + chartWidth * 0.05;

            // Y position based on intensity level
            const yPercent = chartTop + ((100 - intensityYPosition[bubble.intensity]) / 100) * chartHeightPercent;

            // Bubble size: Linear radius proportional to count for better visual discrimination
            const minRadius = compact ? 8 : 10; // Minimum visible size
            const maxRadius = compact ? 40 : 52; // Maximum size for largest bubble

            // Linear interpolation: smallest count gets minRadius, largest gets maxRadius
            const minCount = Math.min(...bubbles.map(b => b.count));
            const countRange = maxCount - minCount || 1;
            const radiusRange = maxRadius - minRadius;

            // Linear scale for radius (not area) - makes differences more visible
            const radius = minRadius + ((bubble.count - minCount) / countRange) * radiusRange;

            const percentage = ((bubble.count / totalQuotes) * 100).toFixed(0);

            return (
              <div
                key={`${bubble.category}-${bubble.intensity}`}
                className="absolute group cursor-crosshair transition-all duration-200 hover:scale-110 hover:z-10 rounded-full flex items-center justify-center"
                style={{
                  left: `${xPercent}%`,
                  top: `${yPercent}%`,
                  width: `${radius}px`,
                  height: `${radius}px`,
                  transform: "translate(-50%, -50%)",
                  backgroundColor: `rgba(${colors.rgb}, ${opacity})`,
                  boxShadow: `0 0 ${radius/3}px rgba(${colors.rgb}, 0.3)`,
                }}
              >
                {/* Count label inside bubble */}
                {radius > 20 && (
                  <span className="text-white/90 font-semibold text-[10px] tabular-nums">
                    {bubble.count}
                  </span>
                )}

                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20">
                  <div className="bg-[#18181b] border border-white/10 rounded-lg px-2.5 py-2 shadow-xl shadow-black/50 whitespace-nowrap">
                    <p className={`text-[11px] font-medium ${colors.text}`}>
                      {colors.label}
                    </p>
                    <p className="text-[10px] text-white/60 mt-0.5 capitalize">
                      {bubble.intensity} intensity
                    </p>
                    <div className="text-[10px] text-white/50 mt-1 pt-1 border-t border-white/10 space-y-0.5">
                      <p>{bubble.count} quotes ({percentage}%)</p>
                      {bubble.avgEngagement > 0 && (
                        <p>Avg engagement: {bubble.avgEngagement.toFixed(1)}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}

          {/* X-axis label */}
          <div
            className={`absolute text-white/40 text-center ${compact ? "text-[8px]" : "text-[9px]"}`}
            style={{
              left: `${chartLeft}%`,
              right: `${100 - chartRight}%`,
              bottom: "0"
            }}
          >
            <span>Engagement →</span>
          </div>

          {/* Y-axis label */}
          <div
            className={`absolute text-white/40 ${compact ? "text-[8px]" : "text-[9px]"}`}
            style={{
              left: "2px",
              top: "50%",
              transform: "rotate(-90deg) translateX(-50%)",
              transformOrigin: "left center",
              whiteSpace: "nowrap",
            }}
          >
            Intensity ↑
          </div>
        </div>
      </div>
    </div>
  );
}
