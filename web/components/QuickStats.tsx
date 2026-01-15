"use client";

import { OverallSentiment, WeeklyTrends, DailyTrends, CategoryTrend } from "@/types";

type Trends = WeeklyTrends | DailyTrends;

interface QuickStatsProps {
  sentiment: OverallSentiment;
  trends?: Trends | null;
}

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

const categoryLabels: Record<CategoryKey, string> = {
  fears: "Fears",
  frustrations: "Frustrations",
  goals: "Goals",
  aspirations: "Aspirations",
};

const categoryColors: Record<CategoryKey, { fill: string; stroke: string; text: string }> = {
  fears: { fill: "rgba(168, 85, 247, 0.15)", stroke: "#a855f7", text: "text-purple-400" },
  frustrations: { fill: "rgba(239, 68, 68, 0.15)", stroke: "#ef4444", text: "text-red-400" },
  goals: { fill: "rgba(59, 130, 246, 0.15)", stroke: "#3b82f6", text: "text-blue-400" },
  aspirations: { fill: "rgba(34, 197, 94, 0.15)", stroke: "#22c55e", text: "text-green-400" },
};

// Type guard to check if trends has data
function hasPreviousData(trends: Trends): boolean {
  if ("has_previous_week" in trends) {
    return trends.has_previous_week;
  }
  return trends.has_previous_day;
}

// Radar chart component
interface RadarChartProps {
  values: number[]; // 4 values (0-1 normalized) for fears, frustrations, goals, aspirations
  previousValues?: number[]; // Optional previous period values
  labels: string[];
  size?: number;
}

function RadarChart({ values, previousValues, labels, size = 160 }: RadarChartProps) {
  const center = size / 2;
  const radius = (size / 2) - 16; // Leave room for labels (reduced from 24)
  const angleStep = (2 * Math.PI) / 4;
  const startAngle = -Math.PI / 2; // Start from top

  // Calculate point positions
  const getPoint = (value: number, index: number) => {
    const angle = startAngle + index * angleStep;
    const r = radius * value;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  };

  // Generate polygon points
  const generatePolygon = (vals: number[]) => {
    return vals.map((v, i) => getPoint(v, i)).map(p => `${p.x},${p.y}`).join(" ");
  };

  // Generate grid circles
  const gridLevels = [0.25, 0.5, 0.75, 1];

  // Label positions (closer to the chart - reduced from 16 to 10)
  const labelPositions = labels.map((_, i) => {
    const angle = startAngle + i * angleStep;
    const r = radius + 10;
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
    };
  });

  const colors = Object.values(categoryColors);

  return (
    <svg width={size} height={size} className="mx-auto">
      {/* Grid circles */}
      {gridLevels.map((level) => (
        <circle
          key={level}
          cx={center}
          cy={center}
          r={radius * level}
          fill="none"
          stroke="rgb(63, 63, 70)"
          strokeWidth="1"
          strokeDasharray={level < 1 ? "2,2" : "0"}
        />
      ))}

      {/* Grid lines from center to each axis */}
      {[0, 1, 2, 3].map((i) => {
        const point = getPoint(1, i);
        return (
          <line
            key={i}
            x1={center}
            y1={center}
            x2={point.x}
            y2={point.y}
            stroke="rgb(63, 63, 70)"
            strokeWidth="1"
          />
        );
      })}

      {/* Previous period polygon (if available) */}
      {previousValues && (
        <polygon
          points={generatePolygon(previousValues)}
          fill="none"
          stroke="rgb(113, 113, 122)"
          strokeWidth="1.5"
          strokeDasharray="4,4"
          opacity="0.6"
        />
      )}

      {/* Current period polygon */}
      <polygon
        points={generatePolygon(values)}
        fill="rgba(255, 255, 255, 0.08)"
        stroke="rgb(161, 161, 170)"
        strokeWidth="2"
      />

      {/* Data points with category colors */}
      {values.map((v, i) => {
        const point = getPoint(v, i);
        return (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r="4"
            fill={colors[i].stroke}
            stroke="rgb(24, 24, 27)"
            strokeWidth="2"
          />
        );
      })}

      {/* Labels */}
      {labels.map((label, i) => {
        const pos = labelPositions[i];
        const textAnchor = i === 0 || i === 2 ? "middle" : i === 1 ? "start" : "end";
        const dy = i === 0 ? "-0.3em" : i === 2 ? "0.8em" : "0.3em";
        return (
          <text
            key={i}
            x={pos.x}
            y={pos.y}
            textAnchor={textAnchor}
            dy={dy}
            className={`text-[10px] font-medium fill-current ${colors[i].text}`}
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}

// Trend badge component
function TrendBadge({ trend }: { trend: CategoryTrend | null }) {
  if (!trend) return null;

  const arrow = trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→";
  const colorClass = trend.direction === "up"
    ? "text-red-400"
    : trend.direction === "down"
    ? "text-green-400"
    : "text-zinc-500";

  return (
    <span className={`text-xs ${colorClass} ml-1`}>
      {arrow}{trend.change_pct !== 0 && `${trend.change_pct > 0 ? "+" : ""}${trend.change_pct}%`}
    </span>
  );
}

export function QuickStats({ sentiment, trends }: QuickStatsProps) {
  const categories: { key: CategoryKey; data: typeof sentiment.fears }[] = [
    { key: "fears", data: sentiment.fears },
    { key: "frustrations", data: sentiment.frustrations },
    { key: "goals", data: sentiment.goals },
    { key: "aspirations", data: sentiment.aspirations },
  ];

  // Get trend for a category
  const getTrend = (key: CategoryKey): CategoryTrend | null => {
    if (!trends || !hasPreviousData(trends)) return null;
    return trends[key] || null;
  };

  // Calculate totals
  const stats = categories.map((cat) => {
    const { mild, moderate, strong } = cat.data.intensity_breakdown;
    const total = mild + moderate + strong;
    return { ...cat, total, trend: getTrend(cat.key) };
  });

  const maxCount = Math.max(...stats.map(s => s.total), 1);

  // Normalize values for radar chart (0-1)
  const normalizedValues = stats.map(s => s.total / maxCount);

  // Get previous period values if available
  let previousNormalizedValues: number[] | undefined;
  if (trends && hasPreviousData(trends)) {
    const prevCounts = categories.map(cat => {
      const trend = trends[cat.key];
      return trend?.previous_count ?? 0;
    });
    // Normalize to same scale as current
    previousNormalizedValues = prevCounts.map(c => c / maxCount);
  }

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full flex flex-col">
      {/* Main content: Radar on left, Categories on right */}
      <div className="flex-1 flex gap-6 items-center">
        {/* Radar Chart */}
        <div className="flex items-center justify-center shrink-0">
          <RadarChart
            values={normalizedValues}
            previousValues={previousNormalizedValues}
            labels={["F", "Fr", "G", "A"]}
            size={150}
          />
        </div>

        {/* Categories with counts and trends */}
        <div className="flex-1 flex flex-col justify-center space-y-3">
          {stats.map((stat) => (
            <div key={stat.key} className="flex items-center justify-between">
              <span className={`text-sm font-medium ${categoryColors[stat.key].text}`}>
                {categoryLabels[stat.key]}
              </span>
              <span className="text-sm text-zinc-300">
                {stat.total}
                <TrendBadge trend={stat.trend} />
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}