"use client";

import { useState, useEffect, useRef } from "react";
import { OverallSentiment } from "@/types";

interface InteractiveSummaryProps {
  sentiment: OverallSentiment;
}

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

const categoryConfig: Record<CategoryKey, { label: string; verb: string;}> = {
  fears: { label: "Fears", verb: "Identify Fears"},
  frustrations: { label: "Frustrations", verb: "Uncover Frustrations"},
  goals: { label: "Goals", verb: "Discover Goals"},
  aspirations: { label: "Aspirations", verb: "Reveal Aspirations"},
};

function TypewriterText({ text, onComplete }: { text: string; onComplete?: () => void }) {
  const [displayedText, setDisplayedText] = useState("");
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);

  useEffect(() => {
    if (indexRef.current < text.length) {
      const timeout = setTimeout(() => {
        setDisplayedText(text.slice(0, indexRef.current + 1));
        indexRef.current += 1;
      }, 15); // Speed of typing
      return () => clearTimeout(timeout);
    } else if (!isComplete) {
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

export function InteractiveSummary({ sentiment }: InteractiveSummaryProps) {
  const [activeCategory, setActiveCategory] = useState<CategoryKey | null>(null);
  const [completedCategories, setCompletedCategories] = useState<Set<CategoryKey>>(new Set());
  const [isTyping, setIsTyping] = useState(false);

  const handleCategoryClick = (category: CategoryKey) => {
    if (isTyping) return; // Prevent clicking while typing
    setActiveCategory(category);
    setIsTyping(true);
  };

  const handleTypingComplete = () => {
    setIsTyping(false);
    if (activeCategory) {
      setCompletedCategories((prev) => new Set([...prev, activeCategory]));
    }
  };

  const getSummary = (category: CategoryKey): string => {
    return sentiment[category].summary;
  };

  const categories: CategoryKey[] = ["fears", "frustrations", "goals", "aspirations"];

  return (
    <div className="bg-zinc-900/50 rounded-3xl border border-zinc-800 p-6">
      {/* Category Buttons */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map((cat) => {
          const config = categoryConfig[cat];
          const isActive = activeCategory === cat;
          const isCompleted = completedCategories.has(cat);

          return (
            <button
              key={cat}
              onClick={() => handleCategoryClick(cat)}
              disabled={isTyping && !isActive}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                isActive
                  ? "bg-zinc-700 text-white ring-2 ring-zinc-500"
                  : isCompleted
                    ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                    : "bg-zinc-800/50 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
              } ${isTyping && !isActive ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
            >
              {isCompleted ? config.label : config.verb}
            </button>
          );
        })}
      </div>

      {/* Summary Display */}
      <div className="min-h-[80px]">
        {activeCategory ? (
          <div className="space-y-2">
            <p className="text-sm text-zinc-400 leading-relaxed">
              {completedCategories.has(activeCategory) ? (
                getSummary(activeCategory)
              ) : (
                <TypewriterText text={getSummary(activeCategory)} onComplete={handleTypingComplete} />
              )}
            </p>
          </div>
        ) : (
          <p className="text-sm text-zinc-500 italic">
            Click a button above to generate AI insights for each category...
          </p>
        )}
      </div>
    </div>
  );
}