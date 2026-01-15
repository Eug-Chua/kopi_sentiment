"use client";

import { TrendingTopic, FFGACategory } from "@/types";

interface TrendingThemesProps {
  topics: TrendingTopic[];
}

function getCategoryColor(category: FFGACategory): string {
  switch (category) {
    case "fear": return "bg-purple-500/20 text-purple-400 border-purple-500/30";
    case "frustration": return "bg-red-500/20 text-red-400 border-red-500/30";
    case "goal": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    case "aspiration": return "bg-green-500/20 text-green-400 border-green-500/30";
    default: return "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
  }
}


export function TrendingThemes({ topics }: TrendingThemesProps) {
  if (!topics || topics.length === 0) {
    return (
      <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full">
        <div className="text-sm text-zinc-500 italic">No trending topics</div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full">
      <div className="space-y-2">
        {topics.slice(0, 5).map((topic, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-zinc-600 text-sm font-medium w-4 flex-shrink-0">{i + 1}</span>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm text-white font-medium truncate" title={topic.topic}>
                  {topic.topic}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-1.5 py-0.5 rounded border ${getCategoryColor(topic.dominant_emotion)}`}>
                  {topic.dominant_emotion}
                </span>
                <span className="text-xs text-zinc-500">{topic.mentions}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}