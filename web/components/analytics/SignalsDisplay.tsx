"use client";

import { useState } from "react";
import { Signal, SignalType } from "@/types";

interface SignalsDisplayProps {
  signals: Signal[];
}

function getSignalLabel(type: SignalType): string {
  switch (type) {
    case "high_engagement": return "High Engagement";
    case "emerging_topic": return "Emerging Topic";
    case "intensity_spike": return "Intensity Spike";
    case "volume_spike": return "Volume Spike";
    default: return "Signal";
  }
}

function getUrgencyColor(urgency: string): { bg: string; text: string; border: string } {
  switch (urgency) {
    case "high": return { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/20" };
    case "medium": return { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20" };
    case "low": return { bg: "bg-blue-500/10", text: "text-blue-400", border: "border-blue-500/20" };
    default: return { bg: "bg-white/5", text: "text-white/60", border: "border-white/10" };
  }
}

/**
 * Signals display for analytics page.
 * Shows signals one at a time with navigation, no typewriter animation.
 */
export function SignalsDisplay({ signals }: SignalsDisplayProps) {
  const [currentIndex, setCurrentIndex] = useState<number>(0); // Start at first signal immediately

  if (!signals || signals.length === 0) {
    return (
      <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm p-4">
        <p className="text-white/40 text-sm">No signals detected for this period.</p>
      </div>
    );
  }

  const handleNext = () => {
    if (currentIndex < signals.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      setCurrentIndex(0); // Loop back to start
    }
  };

  const handlePrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    } else {
      setCurrentIndex(signals.length - 1); // Loop to end
    }
  };

  const currentSignal = signals[currentIndex];
  const urgencyColors = getUrgencyColor(currentSignal.urgency);

  return (
    <div className="rounded-xl border border-white/[0.08] bg-black/40 backdrop-blur-sm">
      {/* Header */}
      <div className="p-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] uppercase tracking-wider text-white/40 font-medium">
              Read the Room
            </p>
            <p className="text-xs text-white/30 mt-0.5">
              {signals.length} signal{signals.length !== 1 ? "s" : ""} detected
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Navigation buttons */}
            <button
              onClick={handlePrev}
              className="w-6 h-6 rounded-md bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors"
            >
              ←
            </button>
            <span className="text-[10px] text-white/40 tabular-nums">
              {currentIndex + 1} / {signals.length}
            </span>
            <button
              onClick={handleNext}
              className="w-6 h-6 rounded-md bg-white/5 hover:bg-white/10 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors"
            >
              →
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <div className="space-y-4">
          {/* Signal type and urgency */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] font-medium text-white/50 uppercase tracking-wide px-2 py-0.5 rounded bg-white/5">
              {getSignalLabel(currentSignal.signal_type)}
            </span>
            <span className={`text-[10px] font-medium uppercase tracking-wide px-2 py-0.5 rounded border ${urgencyColors.bg} ${urgencyColors.text} ${urgencyColors.border}`}>
              {currentSignal.urgency.toUpperCase()} PRIORITY
            </span>
          </div>

          {/* Title */}
          <h3 className="text-base font-medium text-white leading-tight">
            {currentSignal.title}
          </h3>

          {/* Description */}
          <p className="text-sm text-white/60 leading-relaxed">
            {currentSignal.description}
          </p>

          {/* Related quotes */}
          {currentSignal.related_quotes.length > 0 && (
            <div className="pt-3 border-t border-white/[0.04] space-y-2">
              <p className="text-[10px] uppercase tracking-wider text-white/30">
                Related Quotes
              </p>
              {currentSignal.related_quotes.slice(0, 2).map((quote, j) => (
                <p key={j} className="text-xs text-white/50 italic pl-3 border-l-2 border-white/10">
                  &ldquo;{quote}&rdquo;
                </p>
              ))}
            </div>
          )}

          {/* Progress dots */}
          <div className="flex items-center justify-center gap-1.5 pt-2">
            {signals.map((_, i) => (
              <button
                key={i}
                onClick={() => setCurrentIndex(i)}
                className={`w-2 h-2 rounded-full transition-all ${
                  i === currentIndex
                    ? "bg-white/60 scale-110"
                    : i < currentIndex
                    ? "bg-white/30 hover:bg-white/40"
                    : "bg-white/10 hover:bg-white/20"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
