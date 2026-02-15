"use client";

import { AnalyticsReport, OverallSentiment, Signal, AllQuotes, DailySentimentScore } from "@/types";
import { SentimentChart } from "./SentimentChart";
import { CategoryHeatmap } from "./CategoryHeatmap";
import { MomentumDisplay } from "./MomentumDisplay";
import { VelocityAlerts } from "./VelocityAlerts";
import { SentimentComposition } from "./SentimentComposition";
import { DivergencePanel } from "./DivergencePanel";
import { EntityTrendsCompact } from "./EntityTrends";
import { SignalsDisplay } from "./SignalsDisplay";

interface AnalyticsDashboardProps {
  report: AnalyticsReport;
  overallSentiment?: OverallSentiment;
  signals?: Signal[];
  quotes?: AllQuotes;
  isDaily?: boolean;
  /** Full historical data points for week-over-week comparison */
  allDataPoints?: DailySentimentScore[];
}

/**
 * Main analytics dashboard combining all trend analysis components.
 * Designed like a Bloomberg terminal for Singapore vibes.
 */
export function AnalyticsDashboard({ report, overallSentiment, signals, quotes, isDaily, allDataPoints }: AnalyticsDashboardProps) {
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Row 1: Sentiment Pulse (wider) + Main Characters + Sentiment Distribution (narrower, stacked) */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 sm:gap-6">
        <div className="md:col-span-3">
          <SentimentChart
            timeseries={report.sentiment_timeseries}
            commentary={report.sentiment_commentary}
            isDaily={isDaily}
          />
        </div>
        <div className="md:col-span-2 flex flex-col gap-4">
          {report.entity_trends && (
            <EntityTrendsCompact report={report.entity_trends} maxEntities={3} todayOnly={isDaily} />
          )}
          <div className="flex-1">
            <CategoryHeatmap overallSentiment={overallSentiment} quotes={quotes} compact />
          </div>
        </div>
      </div>

      {/* Read the Room - Signals display */}
      {signals && signals.length > 0 && (
        <SignalsDisplay signals={signals} />
      )}

      {/* Two column: Momentum tiles + Velocity alerts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        <MomentumDisplay momentum={report.momentum} velocity={report.velocity} isDaily={isDaily} dataPoints={report.sentiment_timeseries.data_points} />
        <VelocityAlerts velocity={report.velocity} />
      </div>

      {/* Two column: Sentiment Composition + Divergence Detection */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6">
        <SentimentComposition
          dataPoints={isDaily ? report.sentiment_timeseries.data_points : (allDataPoints || report.sentiment_timeseries.data_points)}
          isDaily={isDaily}
        />
        <DivergencePanel dataPoints={report.sentiment_timeseries.data_points} />
      </div>

      {/* Methodology note */}
      <div className="text-xs text-white/40 p-2 sm:p-3 bg-white/[0.02] rounded-lg border border-white/[0.04]">
        <span className="text-white/50 font-medium">Methodology: </span>
        {report.methodology}
      </div>
    </div>
  );
}