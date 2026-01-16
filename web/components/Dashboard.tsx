"use client";

import { useState } from "react";
import { WeeklyReport, DailyReport, ReportMode } from "@/types";
import { ModeToggle } from "./ModeToggle";
import { HeatmapQuotesSection } from "./HeatmapQuotesSection";

interface DashboardProps {
  weeklyReport: WeeklyReport;
  dailyReport: DailyReport | null;
  availableDates: string[];
}

export function Dashboard({ weeklyReport, dailyReport }: DashboardProps) {
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
        <div className="flex items-center gap-4">
          <a href="/about" className="text-white-500 hover:text-gray-300 text-sm">
            About
          </a>
          <ModeToggle mode={mode} onModeChange={setMode} />
        </div>
      </div>

      <p className="text-gray-500 mb-6">{getPeriodLabel()}</p>

      {!dailyReport && mode === "daily" && (
        <div className="bg-amber-900/20 border border-amber-700/50 rounded-lg p-4 mb-6">
          <p className="text-amber-400 text-sm">
            No daily report available yet. Showing weekly report instead.
          </p>
        </div>
      )}

      <HeatmapQuotesSection
        sentiment={report.overall_sentiment}
        quotes={report.all_quotes}
        hotPosts={allTopPosts}
        thematicClusters={report.thematic_clusters}
        signals={report.signals}
      />

    </main>
  );
}