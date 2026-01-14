import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { WeeklyInsights } from "@/types";

interface InsightsPanelProps {
  insights: WeeklyInsights | null;
}

export function InsightsPanel({ insights }: InsightsPanelProps) {
  if (!insights) {
    return null;
  }

  return (
    <div className="space-y-4">
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader className="pb-2">
          <CardTitle className="text-lg font-[family-name:var(--font-space-mono)]">
            This Week
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-xl font-medium text-white">{insights.headline}</p>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-muted-foreground">Key Takeaways</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {insights.key_takeaways.map((takeaway, i) => (
                <li key={i} className="text-sm text-white flex items-start gap-2">
                  <span className="text-blue-400 mt-1">•</span>
                  <span>{takeaway}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="border-l-2 border-l-green-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-green-400">Opportunities</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {insights.opportunities.map((opportunity, i) => (
                <li key={i} className="text-sm text-white flex items-start gap-2">
                  <span className="text-green-400 mt-1">+</span>
                  <span>{opportunity}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="border-l-2 border-l-red-500">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-red-400">Risks to Monitor</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {insights.risks.map((risk, i) => (
                <li key={i} className="text-sm text-white flex items-start gap-2">
                  <span className="text-red-400 mt-1">!</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}