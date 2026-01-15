import { WeeklyTrends, DailyTrends, CategoryTrend } from "@/types";

// Union type for both trend types
type Trends = WeeklyTrends | DailyTrends;

interface TrendsDisplayProps {
  trends: Trends | null;
}

function TrendArrow({ direction }: { direction: string }) {
  if (direction === "up") {
    return <span className="text-red-400">↑</span>;
  } else if (direction === "down") {
    return <span className="text-green-400">↓</span>;
  }
  return <span className="text-zinc-500">→</span>;
}

function CompactTrendBadge({ trend, label }: { trend: CategoryTrend | null; label: string }) {
  if (!trend) return null;

  const colorClass = trend.direction === "up"
    ? "text-red-400"
    : trend.direction === "down"
    ? "text-green-400"
    : "text-zinc-500";

  return (
    <div className="flex items-center gap-1 px-2 py-1 bg-zinc-800/50 rounded text-xs">
      <span className="text-zinc-400">{label}</span>
      <TrendArrow direction={trend.direction} />
      <span className={`font-medium ${colorClass}`}>
        {trend.change_pct > 0 ? "+" : ""}{trend.change_pct}%
      </span>
    </div>
  );
}

// Type guard to check if trends is weekly
function isWeeklyTrends(trends: Trends): trends is WeeklyTrends {
  return "has_previous_week" in trends;
}

// Check if trends has data (works for both types)
function hasPreviousData(trends: Trends): boolean {
  if (isWeeklyTrends(trends)) {
    return trends.has_previous_week;
  }
  return trends.has_previous_day;
}

export function TrendsDisplay({ trends }: TrendsDisplayProps) {
  if (!trends || !hasPreviousData(trends)) {
    return null;
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <CompactTrendBadge trend={trends.fears} label="F" />
      <CompactTrendBadge trend={trends.frustrations} label="Fr" />
      <CompactTrendBadge trend={trends.goals} label="G" />
      <CompactTrendBadge trend={trends.aspirations} label="A" />
    </div>
  );
}