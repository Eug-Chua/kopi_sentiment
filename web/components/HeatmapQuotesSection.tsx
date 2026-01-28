"use client";

import { useState, useRef } from "react";
import { OverallSentiment, AllQuotes, Intensity, PostAnalysis, ThematicCluster, AnalyticsReport, Signal, DailySentimentScore } from "@/types";
import { IntensityHeatmap } from "./IntensityHeatmap";
import { HotPostsTicker } from "./HotPostsTicker";
import { CategoryTabs } from "./CategoryTabs";
import { TrendingThemes } from "./TrendingThemes";
import { InteractiveSummary } from "./InteractiveSummary";
import { AnalyticsDashboard } from "./analytics/AnalyticsDashboard";

type CategoryKey = "fears" | "frustrations" | "optimism";

export interface QuoteFilter {
  category: CategoryKey;
  intensity?: Intensity;
}

interface HeatmapQuotesSectionProps {
  sentiment: OverallSentiment;
  quotes: AllQuotes;
  hotPosts: PostAnalysis[];
  thematicClusters?: ThematicCluster[];
  analyticsReport?: AnalyticsReport | null;
  showAnalytics?: boolean;
  onToggleAnalytics?: () => void;
  displayDate?: string;
  isDaily?: boolean;
  signals?: Signal[];
  /** Full historical data points for week-over-week comparison (from daily analytics) */
  allDataPoints?: DailySentimentScore[];
}

export function HeatmapQuotesSection({
  sentiment,
  quotes,
  hotPosts,
  thematicClusters,
  analyticsReport,
  showAnalytics,
  onToggleAnalytics,
  displayDate,
  signals,
  isDaily,
  allDataPoints,
}: HeatmapQuotesSectionProps) {
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

  // If showing analytics, render the analytics dashboard
  if (showAnalytics && analyticsReport) {
    return (
      <>
        {/* Section header with toggle */}
        <section className="mb-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <button
                onClick={onToggleAnalytics}
                className="text-base sm:text-lg font-semibold font-[family-name:var(--font-space-mono)] text-white/50 hover:text-white/70 transition-colors"
              >
                Vibe Check
              </button>
              <span className="text-white/20">|</span>
              <button
                onClick={onToggleAnalytics}
                className="text-base sm:text-lg font-semibold font-[family-name:var(--font-space-mono)] text-white transition-colors"
              >
                Signals
              </button>
            </div>
            {displayDate && (
              <span className="text-white/40 text-xs sm:text-sm">As of {displayDate}</span>
            )}
          </div>
        </section>
        <AnalyticsDashboard report={analyticsReport} overallSentiment={sentiment} signals={signals} quotes={quotes} isDaily={isDaily} allDataPoints={allDataPoints} />
      </>
    );
  }

  return (
    <>
      {/* Section header with toggle */}
      <section className="mb-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <button
              onClick={analyticsReport ? onToggleAnalytics : undefined}
              className={`text-base sm:text-lg font-semibold font-[family-name:var(--font-space-mono)] transition-colors ${
                analyticsReport ? "text-white" : "text-white cursor-default"
              }`}
            >
              Vibe Check
            </button>
            {analyticsReport && (
              <>
                <span className="text-white/20">|</span>
                <button
                  onClick={onToggleAnalytics}
                  className="text-base sm:text-lg font-semibold font-[family-name:var(--font-space-mono)] text-white/50 hover:text-white/70 transition-colors"
                >
                  Signals
                </button>
              </>
            )}
          </div>
          {displayDate && (
            <span className="text-white/40 text-xs sm:text-sm">As of {displayDate}</span>
          )}
        </div>
        <InteractiveSummary sentiment={sentiment} />
      </section>

      <section className="mb-4">
        <HotPostsTicker posts={hotPosts} />
      </section>

      <section className="mb-4">
        <div className="grid grid-cols-1 md:grid-cols-[6fr_5fr] gap-4 items-stretch">
          <div className="flex flex-col">
            <h2 className="text-base sm:text-lg font-semibold mb-3 font-[family-name:var(--font-space-mono)]">Emotional Heatmap</h2>
            <IntensityHeatmap sentiment={sentiment} onCellClick={handleCellClick} className="flex-1" />
          </div>
          <div className="flex flex-col">
            <h2 className="text-base sm:text-lg font-semibold mb-3 font-[family-name:var(--font-space-mono)]">Top Thematic Clusters</h2>
            <TrendingThemes clusters={thematicClusters} />
          </div>
        </div>
      </section>

      <section ref={quotesRef}>
        <h2 className="text-base sm:text-lg font-semibold font-[family-name:var(--font-space-mono)] mb-3">Quotes by Category</h2>
        {/* Filter chip */}
        {filter && (
          <div className="mb-3">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-white/[0.08] border border-white/[0.15] rounded-full text-xs text-white/70">
              <span className="capitalize">{filter.category}</span>
              {filter.intensity && (
                <>
                  <span className="text-white/30">/</span>
                  <span className="capitalize">{filter.intensity}</span>
                </>
              )}
              <button
                onClick={clearFilter}
                className="ml-1 text-white/50 hover:text-white transition-colors"
              >
                x
              </button>
            </span>
          </div>
        )}
        <CategoryTabs quotes={quotes} filter={filter} />
      </section>
    </>
  );
}