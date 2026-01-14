import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { QuoteWithMetadata } from "@/types";

interface QuoteCardProps {
  quote: QuoteWithMetadata;
}

export function QuoteCard({ quote }: QuoteCardProps) {
  const intensityColors = {
    low: "bg-green-100 text-green-800",
    medium: "bg-yellow-100 text-yellow-800",
    high: "bg-red-100 text-red-800",
  };

  return (
    <Card className="mb-3">
      <CardContent className="pt-4">
        <p className="text-white italic mb-3">{quote.text}</p>
        <div className="flex items-center justify-between text-sm text-gray-300 gap-2">
          <div className="flex-1 min-w-0">
            <span className="text-gray-400">r/{quote.subreddit}</span>
            <span className="text-gray-500 mx-2">·</span>
            <span className="truncate">{quote.post_title}</span>
          </div>
          <Badge className={intensityColors[quote.intensity]}>
            {quote.intensity}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
