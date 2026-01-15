"use client";

import { useState } from "react";
import { WeeklyReport, DailyReport, ReportMode, TrendingTopic } from "@/types";
import { ModeToggle } from "./ModeToggle";
import { InsightsPanel } from "./InsightsPanel";
import { TrendsDisplay } from "./TrendsDisplay";
import { SignalsPanel } from "./SignalsPanel";
import { ThemeClusters } from "./ThemeClusters";
import { HeatmapQuotesSection } from "./HeatmapQuotesSection";
import { TrendingThemesComparison } from "./TrendingThemesComparison";

interface DashboardProps {
  weeklyReport: WeeklyReport;
  dailyReport: DailyReport | null;
  availableDates: string[];
  previousWeekTopics: TrendingTopic[];
}

export function Dashboard({ weeklyReport, dailyReport, previousWeekTopics }: DashboardProps) {
  const [mode, setMode] = useState<ReportMode>("weekly");

  // Use the appropriate report based on mode
  const report = mode === "daily" && dailyReport ? dailyReport : weeklyReport;
  const isDaily = mode === "daily" && dailyReport;

  // Collect all top posts from all subreddits and sort by score
  const allTopPosts = report.subreddits
    .flatMap((sub) => sub.top_posts)
    .sort((a, b) => b.score - a.score);

  // Get the period label
  const getPeriodLabel = () => {
    if (isDaily && dailyReport) {
      return dailyReport.report_date;
    }
    return `Week ${weeklyReport.week_id} (${weeklyReport.week_start} to ${weeklyReport.week_end})`;
  };

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-bold font-[family-name:var(--font-space-mono)]">
          Kopi Sentiment
        </h1>
        <ModeToggle mode={mode} onModeChange={setMode} />
      </div>

      <p className="text-gray-500 mb-6">{getPeriodLabel()}</p>

      {!dailyReport && mode === "daily" && (
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-6">
          <p className="text-amber-400 text-sm">
            No daily report available yet. Showing weekly report instead.
          </p>
        </div>
      )}

      {report.insights && (
        <section className="mb-8">
          <InsightsPanel
            insights={report.insights}
            periodLabel={isDaily ? "Today" : "This Week"}
          />
        </section>
      )}

      {/* Trending Themes Comparison - this week vs last week */}
      <section className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold font-[family-name:var(--font-space-mono)]">
            Trending Themes
          </h2>
          {report.trends && <TrendsDisplay trends={report.trends} />}
        </div>
        <TrendingThemesComparison
          currentTopics={report.trending_topics}
          previousTopics={isDaily ? [] : previousWeekTopics}
          currentLabel={isDaily ? "Today" : `This Week (${weeklyReport.week_id})`}
          previousLabel={isDaily ? "Yesterday" : "Last Week (W02)"}
        />
      </section>

      {report.signals && report.signals.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">
            Notable Signals
          </h2>
          <SignalsPanel signals={report.signals} />
        </section>
      )}

      <HeatmapQuotesSection
        sentiment={report.overall_sentiment}
        quotes={report.all_quotes}
        hotPosts={allTopPosts}
      />

      {report.theme_clusters && report.theme_clusters.length > 0 && (
        <section className="mb-8 mt-8">
          <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">
            Theme Clusters
          </h2>
          <ThemeClusters clusters={report.theme_clusters} />
        </section>
      )}
    </main>
  );
}