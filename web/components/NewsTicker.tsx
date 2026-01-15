"use client";

import { TrendingTopic, FFGACategory } from "@/types";

interface NewsTickerProps {
  topics: TrendingTopic[];
}

function getCategoryColor(category: FFGACategory): string {
  switch (category) {
    case "fear": return "text-purple-400";
    case "frustration": return "text-red-400";
    case "goal": return "text-blue-400";
    case "aspiration": return "text-green-400";
    default: return "text-zinc-400";
  }
}

function getSentimentIcon(shift: string): string {
  switch (shift) {
    case "improving": return "↗";
    case "worsening": return "↘";
    default: return "→";
  }
}

function getSentimentColor(shift: string): string {
  switch (shift) {
    case "improving": return "text-green-400";
    case "worsening": return "text-red-400";
    default: return "text-zinc-500";
  }
}

export function NewsTicker({ topics }: NewsTickerProps) {
  if (!topics || topics.length === 0) {
    return null;
  }

  // Duplicate topics for seamless loop
  const tickerContent = [...topics, ...topics];

  return (
    <div className="bg-zinc-900/50 rounded-lg border border-zinc-800 overflow-hidden">
      <div className="flex items-center">
        <div className="flex-1 overflow-hidden">
          <div className="ticker-wrapper">
            <div className="ticker-content">
              {tickerContent.map((topic, i) => (
                <span key={i} className="ticker-item">
                  <span className={`${getCategoryColor(topic.dominant_emotion)}`}>●</span>
                  <span className="text-white">{topic.topic}</span>
                  <span className="text-zinc-500 text-xs">({topic.mentions})</span>
                  <span className={getSentimentColor(topic.sentiment_shift)}>
                    {getSentimentIcon(topic.sentiment_shift)}
                  </span>
                  <span className="text-zinc-700 mx-4">|</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
      <style jsx>{`
        .ticker-wrapper {
          display: flex;
          width: 100%;
          overflow: hidden;
        }
        .ticker-content {
          display: flex;
          animation: ticker 30s linear infinite;
          white-space: nowrap;
          padding: 8px 0;
        }
        .ticker-item {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
        }
        @keyframes ticker {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        .ticker-wrapper:hover .ticker-content {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}