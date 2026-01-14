"use client";

import { useState, useRef } from "react";
import { OverallSentiment, AllQuotes, Intensity } from "@/types";
import { IntensityHeatmap } from "./IntensityHeatmap";
import { TrendingTopics } from "./TrendingTopics";
import { CategoryTabs } from "./CategoryTabs";
import { TrendingTopic } from "@/types";

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

export interface QuoteFilter {
  category: CategoryKey;
  intensity: Intensity;
}

interface HeatmapQuotesSectionProps {
  sentiment: OverallSentiment;
  topics: TrendingTopic[];
  quotes: AllQuotes;
}

export function HeatmapQuotesSection({ sentiment, topics, quotes }: HeatmapQuotesSectionProps) {
  const [filter, setFilter] = useState<QuoteFilter | null>(null);
  const quotesRef = useRef<HTMLDivElement>(null);

  const handleCellClick = (category: CategoryKey, intensity: Intensity) => {
    setFilter({ category, intensity });
    // Scroll to quotes section
    setTimeout(() => {
      quotesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  };

  const clearFilter = () => {
    setFilter(null);
  };

  return (
    <>
      <section className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-4">
          <div>
            <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Intensity Heatmap</h2>
            <IntensityHeatmap sentiment={sentiment} onCellClick={handleCellClick} />
          </div>
          <div>
            <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Trending Topics</h2>
            <TrendingTopics topics={topics} />
          </div>
        </div>
      </section>

      <section ref={quotesRef}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold font-[family-name:var(--font-space-mono)]">Quotes by Category</h2>
          {filter && (
            <button
              onClick={clearFilter}
              className="text-sm text-zinc-400 hover:text-white flex items-center gap-1 transition-colors"
            >
              <span className="text-xs">Filtering: {filter.category} / {filter.intensity}</span>
              <span className="ml-1">×</span>
            </button>
          )}
        </div>
        <CategoryTabs quotes={quotes} filter={filter} />
      </section>
    </>
  );
}