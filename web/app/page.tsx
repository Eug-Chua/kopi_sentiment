import { WeeklyReport, DailyReport, TrendingTopic } from "@/types";
import { Dashboard } from "@/components/Dashboard";

async function getWeeklyReport(): Promise<WeeklyReport> {
  // In static export, we read from the public folder
  // This works at build time - Next.js will fetch the JSON and embed the data
  const fs = await import("fs/promises");
  const path = await import("path");

  const filePath = path.join(process.cwd(), "public/data/weekly/2026-W03.json");
  const data = await fs.readFile(filePath, "utf-8");
  return JSON.parse(data);
}

async function getPreviousWeekTopics(): Promise<TrendingTopic[]> {
  const fs = await import("fs/promises");
  const path = await import("path");

  try {
    const filePath = path.join(process.cwd(), "public/data/weekly/2026-W02.json");
    const data = await fs.readFile(filePath, "utf-8");
    const report = JSON.parse(data) as WeeklyReport;
    return report.trending_topics || [];
  } catch {
    return [];
  }
}

async function getLatestDailyReport(): Promise<DailyReport | null> {
  const fs = await import("fs/promises");
  const path = await import("path");

  try {
    const dailyDir = path.join(process.cwd(), "public/data/daily");

    // Check if directory exists
    try {
      await fs.access(dailyDir);
    } catch {
      return null;
    }

    // Get all daily report files
    const files = await fs.readdir(dailyDir);
    const jsonFiles = files.filter((f) => f.endsWith(".json")).sort().reverse();

    if (jsonFiles.length === 0) {
      return null;
    }

    // Load the most recent daily report
    const latestFile = jsonFiles[0];
    const filePath = path.join(dailyDir, latestFile);
    const data = await fs.readFile(filePath, "utf-8");
    return JSON.parse(data);
  } catch (error) {
    console.error("Error loading daily report:", error);
    return null;
  }
}

async function getAvailableDates(): Promise<string[]> {
  const fs = await import("fs/promises");
  const path = await import("path");

  try {
    const dailyDir = path.join(process.cwd(), "public/data/daily");

    try {
      await fs.access(dailyDir);
    } catch {
      return [];
    }

    const files = await fs.readdir(dailyDir);
    return files
      .filter((f) => f.endsWith(".json"))
      .map((f) => f.replace(".json", ""))
      .sort()
      .reverse();
  } catch {
    return [];
  }
}

export default async function Page() {
  const [weeklyReport, dailyReport, availableDates, previousWeekTopics] = await Promise.all([
    getWeeklyReport(),
    getLatestDailyReport(),
    getAvailableDates(),
    getPreviousWeekTopics(),
  ]);

  return (
    <Dashboard
      weeklyReport={weeklyReport}
      dailyReport={dailyReport}
      availableDates={availableDates}
      previousWeekTopics={previousWeekTopics}
    />
  );
}