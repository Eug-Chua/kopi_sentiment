import { WeeklyReport } from "@/types";
import { SentimentSummary } from "@/components/SentimentSummary";
import { CategoryTabs } from "@/components/CategoryTabs";

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

  return (
    <main className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-2 font-[family-name:var(--font-space-mono)]">Kopi Sentiment</h1>
      <p className="text-gray-500 mb-6">
        Week {report.week_id} ({report.week_start} to {report.week_end})
      </p>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Weekly Summary</h2>
        <SentimentSummary sentiment={report.overall_sentiment} />
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-4 font-[family-name:var(--font-space-mono)]">Quotes by Category</h2>
        <CategoryTabs quotes={report.all_quotes} />
      </section>
    </main>
  );
}
