"use client";

import { ThematicCluster } from "@/types";

interface TrendingThemesProps {
  clusters?: ThematicCluster[];
}

function formatEngagement(value: number): string {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k`;
  }
  return value.toString();
}

export function TrendingThemes({ clusters }: TrendingThemesProps) {
  const items = clusters || [];

  if (!items || items.length === 0) {
    return (
      <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full flex flex-col">
        <div className="text-sm text-zinc-500 italic">No thematic clusters</div>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full flex flex-col">
      <div className="space-y-2 flex-1 flex flex-col justify-between">
        {items.slice(0, 5).map((item, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-zinc-600 text-sm font-medium w-4 flex-shrink-0">{i + 1}</span>
            <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
              <span className="text-sm text-white font-medium truncate" title={item.topic}>
                {item.topic}
              </span>
              <span className="text-xs text-zinc-500 flex-shrink-0">↑{formatEngagement(item.engagement_score)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}