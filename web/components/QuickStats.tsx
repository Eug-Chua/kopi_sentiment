"use client";

import { OverallSentiment } from "@/types";

interface QuickStatsProps {
  sentiment: OverallSentiment;
}

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

const categoryLabels: Record<CategoryKey, string> = {
  fears: "Fears",
  frustrations: "Frustrations",
  goals: "Goals",
  aspirations: "Aspirations",
};

const categoryColors: Record<CategoryKey, string> = {
  fears: "text-purple-400",
  frustrations: "text-red-400",
  goals: "text-blue-400",
  aspirations: "text-green-400",
};

const categoryBgColors: Record<CategoryKey, string> = {
  fears: "bg-purple-500/20",
  frustrations: "bg-red-500/20",
  goals: "bg-blue-500/20",
  aspirations: "bg-green-500/20",
};

export function QuickStats({ sentiment }: QuickStatsProps) {
  const categories: { key: CategoryKey; data: typeof sentiment.fears }[] = [
    { key: "fears", data: sentiment.fears },
    { key: "frustrations", data: sentiment.frustrations },
    { key: "goals", data: sentiment.goals },
    { key: "aspirations", data: sentiment.aspirations },
  ];

  // Calculate totals and find dominant
  const stats = categories.map((cat) => {
    const { mild, moderate, strong } = cat.data.intensity_breakdown;
    const total = mild + moderate + strong;
    const strongPct = total > 0 ? Math.round((strong / total) * 100) : 0;
    return { ...cat, total, strongPct };
  });

  const totalQuotes = stats.reduce((sum, s) => sum + s.total, 0);
  const dominant = stats.reduce((max, s) => (s.total > max.total ? s : max), stats[0]);
  const mostIntense = stats.reduce((max, s) => (s.strongPct > max.strongPct ? s : max), stats[0]);

  // Calculate overall intensity distribution
  const allStrong = stats.reduce((sum, s) => sum + s.data.intensity_breakdown.strong, 0);
  const allModerate = stats.reduce((sum, s) => sum + s.data.intensity_breakdown.moderate, 0);
  const allMild = stats.reduce((sum, s) => sum + s.data.intensity_breakdown.mild, 0);

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800 h-full flex flex-col justify-between">
      <div className="space-y-4">
        {/* Dominant Emotion */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-1">Dominant This Week</div>
          <div className={`text-lg font-semibold ${categoryColors[dominant.key]}`}>
            {categoryLabels[dominant.key]}
          </div>
          <div className="text-xs text-zinc-400">{dominant.total} quotes ({Math.round((dominant.total / totalQuotes) * 100)}%)</div>
        </div>

        {/* Most Intense */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-1">Highest Intensity</div>
          <div className={`text-base font-medium ${categoryColors[mostIntense.key]}`}>
            {categoryLabels[mostIntense.key]}
          </div>
          <div className="text-xs text-zinc-400">{mostIntense.strongPct}% strong sentiment</div>
        </div>

        {/* Intensity Bar */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-zinc-500 mb-2">Overall Intensity</div>
          <div className="flex h-2 rounded-full overflow-hidden bg-zinc-800">
            <div
              className="bg-zinc-400"
              style={{ width: `${(allMild / totalQuotes) * 100}%` }}
              title={`Mild: ${allMild}`}
            />
            <div
              className="bg-amber-500"
              style={{ width: `${(allModerate / totalQuotes) * 100}%` }}
              title={`Moderate: ${allModerate}`}
            />
            <div
              className="bg-red-500"
              style={{ width: `${(allStrong / totalQuotes) * 100}%` }}
              title={`Strong: ${allStrong}`}
            />
          </div>
          <div className="flex justify-between text-[10px] text-zinc-500 mt-1">
            <span>Mild {Math.round((allMild / totalQuotes) * 100)}%</span>
            <span>Strong {Math.round((allStrong / totalQuotes) * 100)}%</span>
          </div>
        </div>
      </div>

      {/* Total */}
      <div className="pt-3 border-t border-zinc-800 mt-4">
        <div className="flex items-baseline justify-between">
          <span className="text-[10px] uppercase tracking-wider text-zinc-500">Total Analyzed</span>
          <span className="text-2xl font-bold text-white">{totalQuotes}</span>
        </div>
      </div>
    </div>
  );
}