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
    <div className="bg-black/30 rounded-lg px-2.5 sm:px-3 py-2 sm:py-1.5 mb-2 border border-white/[0.06]">
      <div className="flex justify-between items-start gap-2 mb-1.5 sm:mb-1">
        <p className="text-white/70 text-sm sm:text-base italic leading-snug flex-1">{quote.text}</p>
        {quote.comment_score !== undefined && quote.comment_score !== 0 && (
          <span className="text-white/40 text-[10px] flex-shrink-0">
            {quote.comment_score > 0 ? `↑${quote.comment_score}` : `↓${Math.abs(quote.comment_score)}`}
          </span>
        )}
      </div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-[11px] sm:text-xs text-white/40 gap-1 sm:gap-2">
        <div className="flex-1 min-w-0 flex items-center">
          <span className="text-white/40 flex-shrink-0">r/{quote.subreddit}</span>
          <span className="text-white/20 mx-1 flex-shrink-0">·</span>
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
        <Badge className={`flex-shrink-0 text-[9px] px-1.5 py-0.5 h-auto w-fit ${intensityColors[quote.intensity]}`}>
          {quote.intensity}
        </Badge>
      </div>
    </div>
  );
}