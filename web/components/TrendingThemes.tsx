"use client";

import { useState } from "react";
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

const emotionConfig: Record<string, { color: string; label: string }> = {
  fear: { color: "text-red-400/70", label: "Fear" },
  frustration: { color: "text-orange-400/70", label: "Frustration" },
  optimism: { color: "text-emerald-400/70", label: "Optimism" },
};

export function TrendingThemes({ clusters }: TrendingThemesProps) {
  const [selectedCluster, setSelectedCluster] = useState<ThematicCluster | null>(null);
  const [popoverPosition, setPopoverPosition] = useState<{ top: number; left: number } | null>(null);
  const items = clusters || [];

  if (!items || items.length === 0) {
    return (
      <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full flex flex-col">
        <div className="text-sm text-zinc-500 italic">No thematic clusters</div>
      </div>
    );
  }

  const handleClick = (item: ThematicCluster, event: React.MouseEvent) => {
    if (selectedCluster?.topic === item.topic) {
      setSelectedCluster(null);
      setPopoverPosition(null);
    } else {
      const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
      setPopoverPosition({
        top: rect.top,
        left: rect.left + rect.width / 2,
      });
      setSelectedCluster(item);
    }
  };

  const handleClose = () => {
    setSelectedCluster(null);
    setPopoverPosition(null);
  };

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full flex flex-col">
      <div className="space-y-2 flex-1 flex flex-col justify-between">
        {items.slice(0, 5).map((item, i) => (
          <button
            key={i}
            onClick={(e) => handleClick(item, e)}
            className="flex items-start gap-2 text-left w-full hover:bg-white/5 rounded-md p-1 -m-1 transition-colors cursor-pointer"
          >
            <span className="text-zinc-600 text-sm font-medium w-4 flex-shrink-0">{i + 1}</span>
            <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
              <span className="text-sm text-white font-medium truncate hover:text-zinc-300" title={item.topic}>
                {item.topic}
              </span>
              <span className="text-xs text-zinc-500 flex-shrink-0">↑{formatEngagement(item.engagement_score)}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Popover */}
      {selectedCluster && popoverPosition && (
        <ThemePopover
          cluster={selectedCluster}
          onClose={handleClose}
          position={popoverPosition}
        />
      )}
    </div>
  );
}

interface ThemePopoverProps {
  cluster: ThematicCluster;
  onClose: () => void;
  position: { top: number; left: number };
}

function ThemePopover({ cluster, onClose, position }: ThemePopoverProps) {
  const config = emotionConfig[cluster.dominant_emotion] || emotionConfig.frustration;

  return (
    <>
      {/* Invisible backdrop to catch outside clicks */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Popover - positioned over clicked item */}
      <div
        className="fixed w-80 z-50 rounded-lg border border-zinc-700/50 bg-zinc-800/95 backdrop-blur-sm shadow-lg"
        style={{
          top: position.top,
          left: position.left,
          transform: 'translate(-50%, -50%)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-4">
          {/* Header */}
          <div className="flex items-center justify-between gap-2 mb-2">
            <span className={`text-[10px] uppercase tracking-wider font-medium ${config.color}`}>
              {config.label}
            </span>
            <span className="text-[10px] text-zinc-500">
              ↑{formatEngagement(cluster.engagement_score)}
            </span>
          </div>

          {/* Topic title */}
          <h3 className="text-sm font-medium text-zinc-200 mb-3">
            {cluster.topic}
          </h3>

          {/* Sample posts */}
          {cluster.sample_posts && cluster.sample_posts.length > 0 && (
            <div className="space-y-2">
              {cluster.sample_posts.slice(0, 2).map((post, i: number) => {
                const title = typeof post === "string" ? post : post.title;
                const url = typeof post === "string" ? null : post.url;

                return (
                  <div
                    key={i}
                    className="text-xs text-zinc-500 pl-2 border-l border-zinc-600/50"
                  >
                    {url ? (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-zinc-300 transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {title}
                      </a>
                    ) : (
                      title
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}