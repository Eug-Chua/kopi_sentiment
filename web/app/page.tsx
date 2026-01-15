import { WeeklyReport } from "@/types";
import { SentimentSummary } from "@/components/SentimentSummary";
import { InsightsPanel } from "@/components/InsightsPanel";
import { TrendsDisplay } from "@/components/TrendsDisplay";
import { SignalsPanel } from "@/components/SignalsPanel";
import { ThemeClusters } from "@/components/ThemeClusters";
import { HeatmapQuotesSection } from "@/components/HeatmapQuotesSection";

async function getWeeklyReport(): Promise<WeeklyReport> {
  // In static export, we read from the public folder
  // This works at build time - Next.js will fetch the JSON and embed the data
  const fs = await import("fs/promises");
  const path = await import("path");

  const filePath = path.join(process.cwd(), "public/data/weekly/2026-W03.json");
  const data = await fs.readFile(filePath, "utf-8");
  return JSON.parse(data);
}

export default async function Dashboard() {
  const report = await getWeeklyReport();

  // Collect all top posts from all subreddits and sort by score
  const allTopPosts = report.subreddits
    .flatMap((sub) => sub.top_posts)
    .sort((a, b) => b.score - a.score);

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-2 font-[family-name:var(--font-space-mono)]">Kopi Sentiment</h1>
      <p className="text-gray-500 mb-6">
        Week {report.week_id} ({report.week_start} to {report.week_end})
      </p>

      <section className="mb-8">
        <InsightsPanel insights={report.insights} />
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Weekly Summary</h2>
        <SentimentSummary sentiment={report.overall_sentiment} />
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Week-over-Week Trends</h2>
        <TrendsDisplay trends={report.trends} />
      </section>

      {report.signals && report.signals.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Notable Signals</h2>
          <SignalsPanel signals={report.signals} />
        </section>
      )}

      <HeatmapQuotesSection
        sentiment={report.overall_sentiment}
        topics={report.trending_topics}
        quotes={report.all_quotes}
        hotPosts={allTopPosts}
      />

      {report.theme_clusters && report.theme_clusters.length > 0 && (
        <section className="mb-8 mt-8">
          <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Theme Clusters</h2>
          <ThemeClusters clusters={report.theme_clusters} />
        </section>
      )}
    </main>
  );
}