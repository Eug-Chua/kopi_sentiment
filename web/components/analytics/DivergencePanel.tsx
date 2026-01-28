"use client";

import { DailySentimentScore } from "@/types";

interface DivergencePanelProps {
  dataPoints: DailySentimentScore[];
}

interface DivergenceSignal {
  type: "attention_without_positivity" | "quiet_improvement" | "momentum_exhaustion" | "volatility_spike";
  title: string;
  description: string;
  severity: "info" | "warning" | "alert";
  metric: string;
}

/**
 * Divergence detection panel for spotting mismatches between metrics.
 * Identifies patterns like "high engagement but falling sentiment".
 */
export function DivergencePanel({ dataPoints }: DivergencePanelProps) {
  const signals = detectDivergences(dataPoints);

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Divergence Signals
            </p>
            <p className="text-xs text-white/30 mt-0.5">Cross-metric pattern detection</p>
          </div>
          {signals.length > 0 && (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-500/20 text-amber-400 border border-amber-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              {signals.length} detected
            </span>
          )}
        </div>
      </div>

      {/* Signals list or empty state */}
      {signals.length === 0 ? (
        <div className="p-6 text-center">
          <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-emerald-500/10 mb-3">
            <span className="text-emerald-400 text-lg">≈</span>
          </div>
          <p className="text-sm text-white/60">Metrics aligned</p>
          <p className="text-[10px] text-white/30 mt-1">No significant divergences detected</p>
        </div>
      ) : (
        <div className="divide-y divide-white/[0.04]">
          {signals.map((signal, i) => (
            <SignalRow key={i} signal={signal} />
          ))}
        </div>
      )}

      {/* Explanation footer */}
      <div className="p-3 border-t border-white/[0.04] text-[10px] text-white/30">
        Divergences indicate when engagement and sentiment move in opposite directions
      </div>
    </div>
  );
}

function SignalRow({ signal }: { signal: DivergenceSignal }) {
  const config = {
    alert: {
      icon: "⚠",
      iconBg: "bg-red-500/10",
      iconColor: "text-red-400",
      borderColor: "border-l-red-500",
    },
    warning: {
      icon: "◐",
      iconBg: "bg-amber-500/10",
      iconColor: "text-amber-400",
      borderColor: "border-l-amber-500",
    },
    info: {
      icon: "○",
      iconBg: "bg-blue-500/10",
      iconColor: "text-blue-400",
      borderColor: "border-l-blue-500/50",
    },
  }[signal.severity];

  return (
    <div className={`px-4 py-3 border-l-2 ${config.borderColor} hover:bg-white/[0.02] transition-colors`}>
      <div className="flex items-start gap-3">
        <div className={`w-7 h-7 rounded-lg ${config.iconBg} flex items-center justify-center shrink-0`}>
          <span className={config.iconColor}>{config.icon}</span>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white/80">{signal.title}</p>
          <p className="text-xs text-white/50 mt-0.5 leading-relaxed">{signal.description}</p>
          <div className="mt-2 flex items-center gap-2">
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/40">
              {signal.metric}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function detectDivergences(dataPoints: DailySentimentScore[]): DivergenceSignal[] {
  const signals: DivergenceSignal[] = [];

  if (dataPoints.length < 3) return signals;

  // Get recent data (last 3 days)
  const recent = dataPoints.slice(-3);
  const earlier = dataPoints.slice(-6, -3);

  if (earlier.length < 3) return signals;

  // Calculate trends
  const recentEngagement = average(recent.map(d => d.total_engagement));
  const earlierEngagement = average(earlier.map(d => d.total_engagement));
  const engagementTrend = (recentEngagement - earlierEngagement) / earlierEngagement;

  const recentSentiment = average(recent.map(d => d.composite_score));
  const earlierSentiment = average(earlier.map(d => d.composite_score));
  const sentimentChange = recentSentiment - earlierSentiment;

  // 1. Attention without positivity: rising engagement, falling sentiment
  if (engagementTrend > 0.1 && sentimentChange < -5) {
    signals.push({
      type: "attention_without_positivity",
      title: "Attention without positivity",
      description: `Engagement up ${(engagementTrend * 100).toFixed(0)}% but sentiment down ${Math.abs(sentimentChange).toFixed(1)} pts. People are talking more, but not happy.`,
      severity: "warning",
      metric: "ENG↑ SENT↓",
    });
  }

  // 2. Quiet improvement: falling engagement, rising sentiment
  if (engagementTrend < -0.1 && sentimentChange > 5) {
    signals.push({
      type: "quiet_improvement",
      title: "Quiet improvement",
      description: `Engagement down ${Math.abs(engagementTrend * 100).toFixed(0)}% but sentiment up ${sentimentChange.toFixed(1)} pts. Less noise, better vibes.`,
      severity: "info",
      metric: "ENG↓ SENT↑",
    });
  }

  // 3. Volatility spike: check standard deviation of recent composite scores
  const recentScores = recent.map(d => d.composite_score);
  const recentStdDev = stdDev(recentScores);
  const allStdDev = stdDev(dataPoints.map(d => d.composite_score));

  if (recentStdDev > allStdDev * 1.5) {
    signals.push({
      type: "volatility_spike",
      title: "Volatility spike",
      description: `Recent sentiment variance (${recentStdDev.toFixed(1)}) is ${(recentStdDev / allStdDev).toFixed(1)}x higher than normal. Mood swings detected.`,
      severity: "warning",
      metric: "σ SPIKE",
    });
  }

  // 4. Category dominance shift
  const latestData = dataPoints[dataPoints.length - 1];
  const zscores = {
    fears: Math.abs(latestData.fears_zscore_sum),
    frustrations: Math.abs(latestData.frustrations_zscore_sum),
    optimism: Math.abs(latestData.optimism_zscore_sum),
  };

  const totalZScore = Object.values(zscores).reduce((a, b) => a + b, 0);
  const dominant = Object.entries(zscores).reduce((a, b) => a[1] > b[1] ? a : b);
  const dominanceRatio = dominant[1] / totalZScore;

  if (dominanceRatio > 0.4) {
    const categoryName = dominant[0].charAt(0).toUpperCase() + dominant[0].slice(1);
    signals.push({
      type: "momentum_exhaustion",
      title: `${categoryName} dominance`,
      description: `${categoryName} accounts for ${(dominanceRatio * 100).toFixed(0)}% of sentiment intensity today. Single emotion driving the vibe.`,
      severity: "info",
      metric: `${dominant[0].toUpperCase().slice(0, 3)} ${(dominanceRatio * 100).toFixed(0)}%`,
    });
  }

  return signals;
}

function average(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function stdDev(arr: number[]): number {
  const avg = average(arr);
  const squareDiffs = arr.map(value => Math.pow(value - avg, 2));
  return Math.sqrt(average(squareDiffs));
}