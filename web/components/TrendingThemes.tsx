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
  const items = clusters || [];

  if (!items || items.length === 0) {
    return (
      <div className="bg-black/40 backdrop-blur-sm rounded-xl p-4 border border-white/[0.08] h-full flex flex-col">
        <div className="text-sm text-white/40 italic">No thematic clusters</div>
      </div>
    );
  }

  const handleClick = (item: ThematicCluster) => {
    if (selectedCluster?.topic === item.topic) {
      setSelectedCluster(null);
    } else {
      setSelectedCluster(item);
    }
  };

  const handleClose = () => {
    setSelectedCluster(null);
  };

  return (
    <div className="bg-black/40 backdrop-blur-sm rounded-xl p-4 border border-white/[0.08] h-full flex flex-col">
      <div className="space-y-2 flex-1 flex flex-col justify-between">
        {items.slice(0, 5).map((item, i) => (
          <button
            key={i}
            onClick={() => handleClick(item)}
            className="flex items-start gap-2 text-left w-full hover:bg-white/[0.03] rounded-md p-1 -m-1 transition-colors cursor-pointer"
          >
            <span className="text-white/30 text-sm font-medium w-4 flex-shrink-0">{i + 1}</span>
            <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
              <span className="text-sm text-white/80 font-medium truncate hover:text-white" title={item.topic}>
                {item.topic}
              </span>
              <span className="text-xs text-white/40 flex-shrink-0">↑{formatEngagement(item.engagement_score)}</span>
            </div>
          </button>
        ))}
      </div>

      {/* Modal */}
      {selectedCluster && (
        <ThemeModal
          cluster={selectedCluster}
          onClose={handleClose}
        />
      )}
    </div>
  );
}

interface ThemeModalProps {
  cluster: ThematicCluster;
  onClose: () => void;
}

function ThemeModal({ cluster, onClose }: ThemeModalProps) {
  const config = emotionConfig[cluster.dominant_emotion] || emotionConfig.frustration;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal - centered on screen */}
      <div
        className="fixed z-50 w-[90vw] max-w-sm rounded-xl border border-white/[0.1] bg-[#0a0a0a] shadow-xl"
        style={{
          top: '50%',
          left: '50%',
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
            <button
              onClick={onClose}
              className="text-white/40 hover:text-white/70 text-lg leading-none"
            >
              ×
            </button>
          </div>

          {/* Topic title */}
          <h3 className="text-sm font-medium text-white/80 mb-1">
            {cluster.topic}
          </h3>

          <div className="text-[10px] text-white/40 mb-3">
            ↑{formatEngagement(cluster.engagement_score)} engagement
          </div>

          {/* Sample posts */}
          {cluster.sample_posts && cluster.sample_posts.length > 0 && (
            <div className="space-y-2">
              {cluster.sample_posts.slice(0, 2).map((post, i: number) => {
                const title = typeof post === "string" ? post : post.title;
                const url = typeof post === "string" ? null : post.url;

                return (
                  <div
                    key={i}
                    className="text-xs text-white/50 pl-2 border-l border-white/[0.1]"
                  >
                    {url ? (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-white transition-colors"
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