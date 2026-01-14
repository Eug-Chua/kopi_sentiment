import { Card, CardContent } from "@/components/ui/card";
import { WeeklyTrends, CategoryTrend } from "@/types";

interface TrendsDisplayProps {
  trends: WeeklyTrends | null;
}

function TrendArrow({ direction }: { direction: string }) {
  if (direction === "up") {
    return <span className="text-red-400">↑</span>;
  } else if (direction === "down") {
    return <span className="text-green-400">↓</span>;
  }
  return <span className="text-gray-400">→</span>;
}

function TrendBadge({ trend, label }: { trend: CategoryTrend | null; label: string }) {
  if (!trend) return null;

  const colorClass = trend.direction === "up"
    ? "text-red-400"
    : trend.direction === "down"
    ? "text-green-400"
    : "text-gray-400";

  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-zinc-800/50 rounded-lg">
      <span className="text-sm text-muted-foreground">{label}</span>
      <TrendArrow direction={trend.direction} />
      <span className={`text-sm font-medium ${colorClass}`}>
        {trend.change_pct > 0 ? "+" : ""}{trend.change_pct}%
      </span>
      <span className="text-xs text-muted-foreground">
        ({trend.previous_count} → {trend.current_count})
      </span>
    </div>
  );
}

export function TrendsDisplay({ trends }: TrendsDisplayProps) {
  if (!trends || !trends.has_previous_week) {
    return (
      <Card className="bg-zinc-900/50">
        <CardContent className="py-4">
          <p className="text-sm text-muted-foreground text-center">
            No previous week data available for trend comparison
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-zinc-900/50">
      <CardContent className="py-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm text-muted-foreground">
            vs {trends.previous_week_id}
          </span>
        </div>
        <div className="flex flex-wrap gap-3">
          <TrendBadge trend={trends.fears} label="Fears" />
          <TrendBadge trend={trends.frustrations} label="Frustrations" />
          <TrendBadge trend={trends.goals} label="Goals" />
          <TrendBadge trend={trends.aspirations} label="Aspirations" />
        </div>
      </CardContent>
    </Card>
  );
}