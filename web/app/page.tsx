import { WeeklyReport, DailyReport, AnalyticsReport } from "@/types";
import { Dashboard } from "@/components/Dashboard";

async function getWeeklyReport(): Promise<WeeklyReport> {
  // In static export, we read from the public folder
  // This works at build time - Next.js will fetch the JSON and embed the data
  const fs = await import("fs/promises");
  const path = await import("path");

  const weeklyDir = path.join(process.cwd(), "public/data/weekly");
  const files = await fs.readdir(weeklyDir);
  const jsonFiles = files.filter((f) => f.endsWith(".json")).sort().reverse();

  // Get the latest weekly report (sorted descending, so first is latest)
  const latestFile = jsonFiles[0];
  const filePath = path.join(weeklyDir, latestFile);
  const data = await fs.readFile(filePath, "utf-8");
  return JSON.parse(data);
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

async function getAnalyticsReport(): Promise<AnalyticsReport | null> {
  const fs = await import("fs/promises");
  const path = await import("path");

  try {
    const filePath = path.join(process.cwd(), "public/data/analytics.json");
    const data = await fs.readFile(filePath, "utf-8");
    return JSON.parse(data);
  } catch {
    return null;
  }
}

async function getWeeklyAnalyticsReport(): Promise<AnalyticsReport | null> {
  const fs = await import("fs/promises");
  const path = await import("path");

  try {
    const filePath = path.join(process.cwd(), "public/data/analytics_weekly.json");
    const data = await fs.readFile(filePath, "utf-8");
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export default async function Page() {
  const [weeklyReport, dailyReport, availableDates, analyticsReport, weeklyAnalyticsReport] = await Promise.all([
    getWeeklyReport(),
    getLatestDailyReport(),
    getAvailableDates(),
    getAnalyticsReport(),
    getWeeklyAnalyticsReport(),
  ]);

  return (
    <Dashboard
      weeklyReport={weeklyReport}
      dailyReport={dailyReport}
      availableDates={availableDates}
      analyticsReport={analyticsReport}
      weeklyAnalyticsReport={weeklyAnalyticsReport}
    />
  );
}