"use client";

import { useState } from "react";
import { WeeklyReport, DailyReport, ReportMode, AnalyticsReport } from "@/types";
import { ModeToggle } from "./ModeToggle";
import { HeatmapQuotesSection } from "./HeatmapQuotesSection";
import { AnalyticsDashboard } from "./analytics/AnalyticsDashboard";

interface DashboardProps {
  weeklyReport: WeeklyReport;
  dailyReport: DailyReport | null;
  availableDates: string[];
  analyticsReport: AnalyticsReport | null;
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

export function Dashboard({ weeklyReport, dailyReport, analyticsReport }: DashboardProps) {
  const [mode, setMode] = useState<ReportMode>("weekly");
  const [showAnalytics, setShowAnalytics] = useState(false);

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
      return `Updated ${formatDate(dailyReport.report_date)}`;
    }
    // Use generated_at for weekly (when the scrape was run)
    const generatedDate = weeklyReport.generated_at.split("T")[0];
    return `Vibes from the last 7 days till ${formatDate(generatedDate)}`;
  };

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      <div className="flex items-center justify-between mb-2">
        <div>
        <h1 className="text-xl md:text-3xl font-bold font-[family-name:var(--font-space-mono)]">
          Kopi Sentiment
        </h1>
        <p className="text-gray-500 text-xs md:text-sm mt-1">
          Singapore's Reddit in a 5-minute TL;DR.
        </p>
        </div>
        <div className="flex items-center gap-3">
          <a href="about" className="text-gray-400 hover:text-gray-300 text-xs md:text-sm">
            About
          </a>
          <ModeToggle mode={mode} onModeChange={setMode} />
        </div>
      </div>

      <p className="text-gray-500 mb-6 text-xs md:text-base">{getPeriodLabel()}</p>

      {!dailyReport && mode === "daily" && (
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-6">
          <p className="text-amber-400 text-sm">
            No daily report available yet. Showing weekly report instead.
          </p>
        </div>
      )}

      {/* Analytics toggle */}
      {analyticsReport && (
        <div className="mb-6">
          <button
            onClick={() => setShowAnalytics(!showAnalytics)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              showAnalytics
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-300 hover:bg-gray-700"
            }`}
          >
            {showAnalytics ? "← Back to Sentiment" : "📊 View Trend Analytics"}
          </button>
        </div>
      )}

      {/* Conditional rendering: Analytics or main sentiment view */}
      {showAnalytics && analyticsReport ? (
        <AnalyticsDashboard report={analyticsReport} overallSentiment={report.overall_sentiment} signals={dailyReport?.signals} />
      ) : (
        <HeatmapQuotesSection
          sentiment={report.overall_sentiment}
          quotes={report.all_quotes}
          hotPosts={allTopPosts}
          thematicClusters={report.thematic_clusters}
        />
      )}

    </main>
  );
}