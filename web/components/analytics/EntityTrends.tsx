"use client";

import { EntityTrendsReport, EntityTrend } from "@/types";

interface EntityTrendsProps {
  report: EntityTrendsReport;
}

const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
  fear: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  frustration: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
  optimism: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  unknown: { bg: "bg-white/5", text: "text-white/60", border: "border-white/10" },
};

const trendIcons: Record<string, string> = {
  rising: "↗",
  falling: "↘",
  stable: "→",
};

const trendColors: Record<string, string> = {
  rising: "text-emerald-400",
  falling: "text-red-400",
  stable: "text-white/40",
};

/**
 * Entity trends visualization showing top entities with sparklines.
 * Tracks which topics (HDB, CPF, Employment, etc.) are being discussed over time.
 */
export function EntityTrends({ report }: EntityTrendsProps) {
  if (!report.top_entities || report.top_entities.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm p-4">
        <p className="text-white/40 text-sm">No entity data available yet. Run the daily pipeline with the updated prompts to extract entities.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-3 sm:p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Main Characters
            </p>
            <p className="text-xs text-white/30 mt-0.5">
              Main characters by engagement
            </p>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-white/30">
            <span className="flex items-center gap-1">
              <span className="text-emerald-400">↗</span> Rising
            </span>
            <span className="flex items-center gap-1">
              <span className="text-red-400">↘</span> Falling
            </span>
          </div>
        </div>
      </div>

      {/* Entity list */}
      <div className="p-4 space-y-3">
        {report.top_entities.slice(0, 10).map((entity, index) => (
          <EntityRow key={entity.entity} entity={entity} rank={index + 1} />
        ))}
      </div>
    </div>
  );
}

interface EntityRowProps {
  entity: EntityTrend;
  rank: number;
}

function EntityRow({ entity, rank }: EntityRowProps) {
  const colors = categoryColors[entity.dominant_category] || categoryColors.unknown;
  const trendColor = trendColors[entity.trend_direction];
  const trendIcon = trendIcons[entity.trend_direction];

  // Calculate sparkline data (normalize to 0-100)
  const maxEngagement = Math.max(...entity.daily_data.map((d) => d.engagement), 1);
  const sparklineData = entity.daily_data.map((d) => (d.engagement / maxEngagement) * 100);

  return (
    <div className={`rounded-lg p-3 border ${colors.border} ${colors.bg}`}>
      <div className="flex items-center justify-between gap-4">
        {/* Left: Rank, Entity name, Category */}
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-[10px] text-white/30 w-4 flex-shrink-0">
            #{rank}
          </span>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-white truncate">
                {entity.entity}
              </span>
              <span className={`text-[10px] px-1.5 py-0.5 rounded ${colors.bg} ${colors.text} border ${colors.border}`}>
                {entity.dominant_category.slice(0, 3).toUpperCase()}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-0.5 text-[10px] text-white/40">
              <span>{entity.days_present} {entity.days_present === 1 ? "day" : "days"}</span>
            </div>
          </div>
        </div>

        {/* Right: Sparkline, Trend, Engagement */}
        <div className="flex items-center gap-4">
          {/* Sparkline */}
          <Sparkline data={sparklineData} color={colors.text} />

          {/* Trend indicator */}
          <span className={`text-lg ${trendColor}`}>{trendIcon}</span>

          {/* Engagement */}
          <div className="text-right w-16">
            <span className="text-sm font-medium text-white tabular-nums">
              {formatEngagement(entity.total_engagement)}
            </span>
            <p className="text-[9px] text-white/30">engagement</p>
          </div>
        </div>
      </div>
    </div>
  );
}

interface SparklineProps {
  data: number[];
  color: string;
}

function Sparkline({ data, color }: SparklineProps) {
  if (data.length < 2) {
    return <div className="w-16 h-6" />;
  }

  // Create SVG path
  const width = 64;
  const height = 24;
  const padding = 2;

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1)) * (width - 2 * padding);
    const y = height - padding - (value / 100) * (height - 2 * padding);
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(" L ")}`;

  // Extract color class to actual color for SVG
  const strokeColor = color.includes("purple")
    ? "#a855f7"
    : color.includes("red")
    ? "#ef4444"
    : color.includes("blue")
    ? "#3b82f6"
    : color.includes("emerald")
    ? "#10b981"
    : "#9ca3af";

  return (
    <svg width={width} height={height} className="opacity-60">
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End dot */}
      <circle
        cx={points[points.length - 1].split(",")[0]}
        cy={points[points.length - 1].split(",")[1]}
        r="2"
        fill={strokeColor}
      />
    </svg>
  );
}

function formatEngagement(value: number): string {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k`;
  }
  return value.toString();
}

/**
 * Compact version of EntityTrends for side-by-side layout with SentimentChart.
 * Shows top 5 entities in a condensed format.
 */
interface EntityTrendsCompactProps {
  report: EntityTrendsReport;
}

export function EntityTrendsCompact({ report }: EntityTrendsCompactProps) {
  if (!report.top_entities || report.top_entities.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm p-4">
        <p className="text-white/40 text-sm">No topic data available.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Main Characters
            </p>
            <p className="text-xs text-white/30 mt-0.5">
              Sorted by topic cluster upvotes
            </p>
          </div>
          <div className="flex items-center gap-2 text-[9px] text-white/30">
            <span className="flex items-center gap-1">
              <span className="text-emerald-400">↗</span> Rising
            </span>
            <span className="flex items-center gap-1">
              <span className="text-red-400">↘</span> Falling
            </span>
          </div>
        </div>
      </div>

      {/* Compact entity list */}
      <div className="p-3 space-y-2 flex-1">
        {report.top_entities.slice(0, 8).map((entity, index) => (
          <EntityRowCompact key={entity.entity} entity={entity} rank={index + 1} />
        ))}
      </div>
    </div>
  );
}

function EntityRowCompact({ entity, rank }: EntityRowProps) {
  const colors = categoryColors[entity.dominant_category] || categoryColors.unknown;
  const trendColor = trendColors[entity.trend_direction];
  const trendIcon = trendIcons[entity.trend_direction];

  return (
    <div className={`rounded-lg px-2.5 py-1.5 border ${colors.border} ${colors.bg} flex items-center justify-between gap-2`}>
      {/* Left: Rank + Entity */}
      <div className="flex items-center gap-1.5 min-w-0 flex-1">
        <span className="text-[10px] text-white/30 w-4 flex-shrink-0 text-center">
          {rank}
        </span>
        <span className="text-xs font-medium text-white truncate">
          {entity.entity}
        </span>
        <span className={`text-[8px] px-1 py-0.5 rounded ${colors.bg} ${colors.text} border ${colors.border} flex-shrink-0 uppercase`}>
          {entity.dominant_category.slice(0, 3)}
        </span>
      </div>

      {/* Right: Trend + Engagement */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <span className={`text-sm ${trendColor}`}>{trendIcon}</span>
        <span className="text-[10px] font-medium text-white/60 tabular-nums w-8 text-right">
          {formatEngagement(entity.total_engagement)}
        </span>
      </div>
    </div>
  );
}