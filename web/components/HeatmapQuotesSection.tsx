"use client";

import { useState, useRef } from "react";
import { OverallSentiment, AllQuotes, Intensity, PostAnalysis, Signal, ThematicCluster } from "@/types";
import { IntensityHeatmap } from "./IntensityHeatmap";
import { HotPostsTicker } from "./HotPostsTicker";
import { CategoryTabs } from "./CategoryTabs";
import { TrendingThemes } from "./TrendingThemes";
import { InteractiveSummary } from "./InteractiveSummary";
import { RiskMonitor } from "./RiskMonitor";

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

export interface QuoteFilter {
  category: CategoryKey;
  intensity?: Intensity;
}

interface HeatmapQuotesSectionProps {
  sentiment: OverallSentiment;
  quotes: AllQuotes;
  hotPosts: PostAnalysis[];
  thematicClusters?: ThematicCluster[];
  signals?: Signal[];
}

export function HeatmapQuotesSection({ sentiment, quotes, hotPosts, thematicClusters, signals }: HeatmapQuotesSectionProps) {
  const [filter, setFilter] = useState<QuoteFilter | null>(null);
  const quotesRef = useRef<HTMLDivElement>(null);

  const handleCellClick = (category: CategoryKey, intensity?: Intensity) => {
    setFilter({ category, intensity });
    // Scroll to quotes section
    setTimeout(() => {
      quotesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  };

  const clearFilter = () => {
    setFilter(null);
  };

  const getFilterLabel = () => {
    if (!filter) return "";
    if (filter.intensity) {
      return `${filter.category} / ${filter.intensity}`;
    }
    return `${filter.category} (all)`;
  };

  return (
    <>
      <section className="mb-4">
        <div className="grid grid-cols-1 md:grid-cols-[6fr_5fr] gap-4 items-stretch">
          <div className="flex flex-col">
            <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Emotional Heatmap</h2>
            <IntensityHeatmap sentiment={sentiment} onCellClick={handleCellClick} className="flex-1" />
          </div>
          <div className="flex flex-col">
            <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Thematic Clusters</h2>
            <TrendingThemes clusters={thematicClusters} />
          </div>
        </div>
      </section>

      <section className="mb-4">
        <HotPostsTicker posts={hotPosts} />
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Vibe Check</h2>
        <InteractiveSummary sentiment={sentiment} />
      </section>

      {signals && signals.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">What The People Are Saying</h2>
          <RiskMonitor signals={signals} />
        </section>
      )}

      <section ref={quotesRef}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-2">
          <h2 className="text-lg sm:text-xl font-semibold font-[family-name:var(--font-space-mono)]">Quotes by Category</h2>
          {filter && (
            <button
              onClick={clearFilter}
              className="text-sm text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <span className="text-xs">Filtering: {getFilterLabel()}</span>
              <span className="ml-1">×</span>
            </button>
          )}
        </div>
        <CategoryTabs quotes={quotes} filter={filter} />
      </section>
    </>
  );
}