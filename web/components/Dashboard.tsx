"use client";

import { useState } from "react";
import { WeeklyReport, DailyReport, ReportMode, AnalyticsReport } from "@/types";
import { ModeToggle } from "./ModeToggle";
import { HeatmapQuotesSection } from "./HeatmapQuotesSection";

interface DashboardProps {
  weeklyReport: WeeklyReport;
  dailyReport: DailyReport | null;
  availableDates: string[];
  analyticsReport: AnalyticsReport | null;
  weeklyAnalyticsReport: AnalyticsReport | null;
}

// Format date from "2026-01-18" to "18 Jan 2026"
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function Dashboard({ weeklyReport, dailyReport, analyticsReport, weeklyAnalyticsReport }: DashboardProps) {
  const [mode, setMode] = useState<ReportMode>("weekly");
  const [showAnalytics, setShowAnalytics] = useState(false);

  // Use the appropriate report based on mode
  const report = mode === "daily" && dailyReport ? dailyReport : weeklyReport;
  const isDaily = mode === "daily" && dailyReport;

  // Use the appropriate analytics report based on mode
  const activeAnalyticsReport = isDaily ? analyticsReport : weeklyAnalyticsReport;

  // Collect all top posts from all subreddits and sort by score
  const allTopPosts = report.subreddits
    .flatMap((sub) => sub.top_posts)
    .sort((a, b) => b.score - a.score);

  // Get display date
  const getDisplayDate = () => {
    if (isDaily && dailyReport) {
      return formatDate(dailyReport.report_date);
    }
    const generatedDate = weeklyReport.generated_at.split("T")[0];
    return formatDate(generatedDate);
  };

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      {/* Header - stacks better on mobile */}
      <div className="flex flex-col gap-3 mb-4 sm:mb-6">
        {/* Row 1: Title + Controls */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl sm:text-3xl font-bold font-[family-name:var(--font-space-mono)]">
            Kopi Sentiment
          </h1>
          <div className="flex items-center gap-2 sm:gap-3">
            <a href="about" className="text-gray-400 hover:text-gray-300 text-xs sm:text-sm">
              About
            </a>
            <ModeToggle mode={mode} onModeChange={setMode} />
          </div>
        </div>
        {/* Row 2: Tagline */}
        <p className="text-gray-500 text-xs sm:text-sm">
          Singapore's Reddit in a 5-minute TL;DR.
        </p>
      </div>

      {!dailyReport && mode === "daily" && (
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-6">
          <p className="text-amber-400 text-sm">
            No daily report available yet. Showing weekly report instead.
          </p>
        </div>
      )}

      {/* Main content area with integrated toggle */}
      <HeatmapQuotesSection
        sentiment={report.overall_sentiment}
        quotes={report.all_quotes}
        hotPosts={allTopPosts}
        thematicClusters={report.thematic_clusters}
        analyticsReport={activeAnalyticsReport}
        showAnalytics={showAnalytics}
        onToggleAnalytics={() => setShowAnalytics(!showAnalytics)}
        displayDate={getDisplayDate()}
        isDaily={!!isDaily}
        signals={report.signals}
        allDataPoints={analyticsReport?.sentiment_timeseries?.data_points}
      />

    </main>
  );
}