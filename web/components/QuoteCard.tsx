import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { QuoteWithMetadata } from "@/types";

interface QuoteCardProps {
  quote: QuoteWithMetadata;
}

export function QuoteCard({ quote }: QuoteCardProps) {
  const intensityColors = {
    mild: "bg-zinc-400/70 text-white",
    moderate: "bg-amber-500/70 text-white",
    strong: "bg-red-500/70 text-white",
  };

  return (
    <Card className="mb-3">
      <CardContent className="pt-4">
        <p className="text-white italic mb-3">{quote.text}</p>
        <div className="flex items-center justify-between text-sm text-gray-300 gap-2">
          <div className="flex-1 min-w-0 flex items-center">
            <span className="text-gray-400 flex-shrink-0">r/{quote.subreddit}</span>
            <span className="text-gray-500 mx-2 flex-shrink-0">·</span>
            <span className="truncate" title={quote.post_title}>{quote.post_title}</span>
          </div>
          <Badge className={`flex-shrink-0 ${intensityColors[quote.intensity]}`}>
            {quote.intensity}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
