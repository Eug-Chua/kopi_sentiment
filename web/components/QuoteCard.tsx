import { Badge } from "@/components/ui/badge";
import { QuoteWithMetadata } from "@/types";

interface QuoteCardProps {
  quote: QuoteWithMetadata;
}

function constructRedditUrl(subreddit: string, postId: string): string {
  // Remove 't3_' prefix if present
  const cleanId = postId.replace(/^t3_/, "");
  return `https://reddit.com/r/${subreddit}/comments/${cleanId}`;
}

export function QuoteCard({ quote }: QuoteCardProps) {
  const intensityColors = {
    mild: "bg-zinc-400/70 text-white",
    moderate: "bg-amber-500/70 text-white",
    strong: "bg-red-500/70 text-white",
  };

  const postUrl = constructRedditUrl(quote.subreddit, quote.post_id);

  return (
    <div className="bg-zinc-900/40 rounded px-2.5 py-1.5 mb-2 border border-zinc-800/50">
      <div className="flex justify-between items-start gap-2 mb-1">
        <p className="text-zinc-200 text-base italic leading-snug flex-1">{quote.text}</p>
        {quote.comment_score !== undefined && quote.comment_score > 0 && (
          <span className="text-zinc-500 text-[10px] flex-shrink-0">↑{quote.comment_score}</span>
        )}
      </div>
      <div className="flex items-center justify-between text-[9px] text-gray-500 gap-2">
        <div className="flex-1 min-w-0 flex items-center">
          <span className="text-zinc-600 flex-shrink-0">r/{quote.subreddit}</span>
          <span className="text-zinc-700 mx-1 flex-shrink-0">·</span>
          <a
            href={postUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="truncate hover:text-[#FF4500] transition-colors"
            title={quote.post_title}
          >
            {quote.post_title}
          </a>
        </div>
        <Badge className={`flex-shrink-0 text-[8px] px-1 py-0 h-4 ${intensityColors[quote.intensity]}`}>
          {quote.intensity}
        </Badge>
      </div>
    </div>
  );
}