"use client";

import { AnalyticsReport, OverallSentiment, Signal } from "@/types";
import { SentimentChart } from "./SentimentChart";
import { CategoryHeatmap } from "./CategoryHeatmap";
import { MomentumDisplay } from "./MomentumDisplay";
import { VelocityAlerts } from "./VelocityAlerts";
import { SentimentComposition } from "./MarketBreadth";
import { DivergencePanel } from "./DivergencePanel";
import { EntityTrendsCompact } from "./EntityTrends";
import { SignalsDisplay } from "./SignalsDisplay";

interface AnalyticsDashboardProps {
  report: AnalyticsReport;
  overallSentiment?: OverallSentiment;
  signals?: Signal[];
}

/**
 * Main analytics dashboard combining all trend analysis components.
 * Designed like a Bloomberg terminal for Singapore vibes.
 */
export function AnalyticsDashboard({ report, overallSentiment, signals }: AnalyticsDashboardProps) {
  return (
    <div className="space-y-6">
      {/* Row 1: Sentiment Pulse (wider) + Main Characters (narrower) */}
      <div className="grid md:grid-cols-5 gap-6">
        <div className="md:col-span-3">
          <SentimentChart
            timeseries={report.sentiment_timeseries}
            commentary={report.sentiment_commentary}
          />
        </div>
        {report.entity_trends && (
          <div className="md:col-span-2">
            <EntityTrendsCompact report={report.entity_trends} />
          </div>
        )}
      </div>

      {/* Read the Room - Signals display */}
      {signals && signals.length > 0 && (
        <SignalsDisplay signals={signals} />
      )}

      {/* Category Heatmap - Daily z-score intensity */}
      <CategoryHeatmap dataPoints={report.sentiment_timeseries.data_points} />

      {/* Two column: Momentum tiles + Velocity alerts */}
      <div className="grid md:grid-cols-2 gap-6">
        <MomentumDisplay momentum={report.momentum} />
        <VelocityAlerts velocity={report.velocity} />
      </div>

      {/* Two column: Sentiment Composition + Divergence Detection */}
      <div className="grid md:grid-cols-2 gap-6">
        <SentimentComposition dataPoints={report.sentiment_timeseries.data_points} />
        <DivergencePanel dataPoints={report.sentiment_timeseries.data_points} />
      </div>

      {/* Methodology note */}
      <div className="text-xs text-white/40 p-3 bg-white/[0.02] rounded-lg border border-white/[0.04]">
        <span className="text-white/50 font-medium">Methodology: </span>
        {report.methodology}
      </div>
    </div>
  );
}