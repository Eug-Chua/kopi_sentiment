"use client";

import { useState, useEffect, useRef } from "react";
import { Signal, SignalType } from "@/types";

interface RiskMonitorProps {
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

function getUrgencyColor(urgency: string): string {
  switch (urgency) {
    case "high": return "text-red-400";
    case "medium": return "text-yellow-400";
    case "low": return "text-blue-400";
    default: return "text-zinc-400";
  }
}

function TypewriterText({ text, onComplete }: { text: string; onComplete?: () => void }) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);

  useEffect(() => {
    indexRef.current = 0;
    setDisplayedText("");
    setIsComplete(false);
  }, [text]);

  useEffect(() => {
    if (indexRef.current < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(text.slice(0, indexRef.current + 1));
        indexRef.current += 1;
      }, 15); // Match Vibe Check speed
      return () => clearTimeout(timeout);
    } else if (!isComplete && text.length > 0) {
      setIsComplete(true);
      onComplete?.();
    }
  }, [displayedText, text, isComplete, onComplete]);

  return (
    <span>
      {displayedText}
      {!isComplete && <span className="animate-pulse">|</span>}
    </span>
  );
}

export function RiskMonitor({ signals }: RiskMonitorProps) {
  const [currentIndex, setCurrentIndex] = useState<number>(-1);
  const [isTyping, setIsTyping] = useState(false);
  const [showQuotes, setShowQuotes] = useState(false);

  if (!signals || signals.length === 0) {
    return null;
  }

  const handleAnalyze = () => {
    if (isTyping) return;

    // Move to next signal (cycle back to 0 after last)
    const nextIndex = currentIndex + 1 >= signals.length ? 0 : currentIndex + 1;
    setCurrentIndex(nextIndex);
    setIsTyping(true);
    setShowQuotes(false);
  };

  const handleTypingComplete = () => {
    setIsTyping(false);
    setShowQuotes(true);
  };

  const currentSignal = currentIndex >= 0 ? signals[currentIndex] : null;
  const hasStarted = currentIndex >= 0;
  const isLastSignal = currentIndex === signals.length - 1;

  // Button text changes based on state
  const getButtonText = () => {
    if (!hasStarted) return "Analyze";
    if (isTyping) return "Reading...";
    if (isLastSignal) return "Start Over";
    return "Next Insight";
  };

  return (
    <div className="bg-zinc-900/50 rounded-3xl border border-zinc-800 p-6 min-h-[140px] flex flex-col">
      {!currentSignal ? (
        /* Centered button when no signal selected */
        <div className="flex-1 flex items-center justify-center">
          <button
            onClick={handleAnalyze}
            className="relative px-5 py-2 rounded-full text-sm font-medium transition-all bg-zinc-700 text-white hover:bg-zinc-600 cursor-pointer overflow-hidden"
          >
            <span className="absolute inset-[-1px] rounded-full overflow-hidden">
              <span className="absolute inset-0 animate-[shimmer_3s_ease-in-out_infinite] bg-gradient-to-r from-transparent via-white/50 to-transparent" />
            </span>
            <span className="absolute inset-[1px] rounded-full bg-zinc-700" />
            <span className="relative z-10">Read the Room</span>
          </button>


        </div>
      ) : (
        /* Content when signal is displayed */
        <>
          <div className="flex items-center justify-center gap-3 mb-4">
            <button
              onClick={handleAnalyze}
              disabled={isTyping}
              className={`px-5 py-2 rounded-full text-sm font-medium transition-all ${
                isTyping
                  ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                  : "bg-zinc-700 text-white hover:bg-zinc-600 cursor-pointer"
              }`}
            >
              {getButtonText()}
            </button>

            {/* Progress indicator */}
            <div className="flex items-center gap-1.5">
              {signals.map((_, i) => (
                <div
                  key={i}
                  className={`w-2 h-2 rounded-full transition-colors ${
                    i <= currentIndex ? "bg-zinc-400" : "bg-zinc-700"
                  }`}
                />
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
                {getSignalLabel(currentSignal.signal_type)}
              </span>
              <span className="text-zinc-600">·</span>
              <span className={`text-xs font-medium ${getUrgencyColor(currentSignal.urgency)}`}>
                {currentSignal.urgency.toUpperCase()} PRIORITY
              </span>
            </div>
            <p className="text-base font-medium text-white">
              {currentSignal.title}
            </p>
            <p className="text-sm text-zinc-400 leading-relaxed">
              {showQuotes ? (
                currentSignal.description
              ) : (
                <TypewriterText
                  text={currentSignal.description}
                  onComplete={handleTypingComplete}
                />
              )}
            </p>
            {showQuotes && currentSignal.related_quotes.length > 0 && (
              <div className="pt-2 space-y-1.5 animate-in fade-in duration-300">
                {currentSignal.related_quotes.slice(0, 2).map((quote, j) => (
                  <p key={j} className="text-xs text-zinc-500 italic pl-3 border-l border-zinc-700">
                    "{quote}"
                  </p>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}