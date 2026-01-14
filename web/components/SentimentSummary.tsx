import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { OverallSentiment } from "@/types";

interface SentimentSummaryProps {
  sentiment: OverallSentiment;
}

export function SentimentSummary({ sentiment }: SentimentSummaryProps) {
    const categories = [
        { key: "fears", label: "Fears", summary: sentiment.fears.summary},
        { key: "frustrations", label: "Frustrations", summary: sentiment.frustrations.summary},
        { key: "goals", label: "Goals", summary: sentiment.goals.summary},
        { key: "aspirations", label: "Aspirations", summary: sentiment.aspirations.summary},
      ];
      

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {categories.map((cat) => (
        <Card key={cat.key} className="hover:bg-accent transition-colors cursor-pointer">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">
              {cat.label}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm">{cat.summary}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
