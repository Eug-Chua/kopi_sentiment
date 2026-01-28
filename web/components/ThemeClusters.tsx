import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ThemeCluster, FFOCategory } from "@/types";

interface ThemeClustersProps {
  clusters: ThemeCluster[];
}

function getCategoryColor(category: FFOCategory): string {
  switch (category) {
    case "fear": return "bg-amber-500/20 text-amber-400 border-amber-500/30";
    case "frustration": return "bg-red-500/20 text-red-400 border-red-500/30";
    case "optimism": return "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
    default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
  }
}

function getCategoryLabel(category: FFOCategory): string {
  return category.charAt(0).toUpperCase() + category.slice(1);
}

export function ThemeClusters({ clusters }: ThemeClustersProps) {
  if (!clusters || clusters.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {clusters.map((cluster, i) => (
        <Card key={i} className="bg-zinc-900/50 border-zinc-800">
          <CardHeader className="pb-2">
            <div className="flex items-start justify-between gap-2">
              <CardTitle className="text-base text-white">{cluster.theme}</CardTitle>
              <Badge
                variant="outline"
                className={`text-xs ${getCategoryColor(cluster.category)}`}
              >
                {getCategoryLabel(cluster.category)}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-3">{cluster.description}</p>
            <div className="flex items-center gap-3 text-xs text-zinc-500 mb-3">
              <span>{cluster.quote_count} quotes</span>
              {cluster.avg_score > 0 && (
                <span>avg score: {cluster.avg_score.toFixed(0)}</span>
              )}
            </div>
            {cluster.sample_quotes.length > 0 && (
              <div className="space-y-2">
                {cluster.sample_quotes.slice(0, 2).map((quote, j) => (
                  <p key={j} className="text-xs text-zinc-400 italic pl-3 border-l border-zinc-700">
                    {quote}
                  </p>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}