"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { OverallSentiment } from "@/types";

interface InteractiveSummaryProps {
  sentiment: OverallSentiment;
}

type CategoryKey = "fears" | "frustrations" | "optimism";

const categoryConfig: Record<CategoryKey, { label: string }> = {
  fears: { label: "Fears" },
  frustrations: { label: "Frustrations" },
  optimism: { label: "Optimism" },
};

const categories: CategoryKey[] = ["fears", "frustrations", "optimism"];

export function InteractiveSummary({ sentiment }: InteractiveSummaryProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const carouselRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeft, setScrollLeft] = useState(0);

  const scrollToIndex = useCallback((index: number) => {
    if (carouselRef.current) {
      const cardWidth = carouselRef.current.offsetWidth;
      carouselRef.current.scrollTo({
        left: cardWidth * index,
        behavior: "smooth",
      });
    }
  }, []);

  const handleDotClick = (index: number) => {
    setActiveIndex(index);
    scrollToIndex(index);
  };

  const handlePrev = () => {
    const newIndex = activeIndex > 0 ? activeIndex - 1 : categories.length - 1;
    setActiveIndex(newIndex);
    scrollToIndex(newIndex);
  };

  const handleNext = () => {
    const newIndex = activeIndex < categories.length - 1 ? activeIndex + 1 : 0;
    setActiveIndex(newIndex);
    scrollToIndex(newIndex);
  };

  // Handle scroll snap to update active index
  const handleScroll = useCallback(() => {
    if (carouselRef.current && !isDragging) {
      const cardWidth = carouselRef.current.offsetWidth;
      const scrollPosition = carouselRef.current.scrollLeft;
      const newIndex = Math.round(scrollPosition / cardWidth);
      if (newIndex !== activeIndex && newIndex >= 0 && newIndex < categories.length) {
        setActiveIndex(newIndex);
      }
    }
  }, [activeIndex, isDragging]);

  // Mouse drag handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!carouselRef.current) return;
    setIsDragging(true);
    setStartX(e.pageX - carouselRef.current.offsetLeft);
    setScrollLeft(carouselRef.current.scrollLeft);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !carouselRef.current) return;
    e.preventDefault();
    const x = e.pageX - carouselRef.current.offsetLeft;
    const walk = (x - startX) * 1.5;
    carouselRef.current.scrollLeft = scrollLeft - walk;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
  };

  // Touch handlers for mobile
  const handleTouchStart = (e: React.TouchEvent) => {
    if (!carouselRef.current) return;
    setStartX(e.touches[0].pageX - carouselRef.current.offsetLeft);
    setScrollLeft(carouselRef.current.scrollLeft);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!carouselRef.current) return;
    const x = e.touches[0].pageX - carouselRef.current.offsetLeft;
    const walk = (x - startX) * 1.5;
    carouselRef.current.scrollLeft = scrollLeft - walk;
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowLeft") {
        handlePrev();
      } else if (e.key === "ArrowRight") {
        handleNext();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeIndex]);

  return (
    <div className="bg-zinc-900/50 rounded-2xl border border-zinc-800 p-4">
      {/* Carousel container */}
      <div className="relative">
        {/* Navigation arrows */}
        <button
          onClick={handlePrev}
          className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-2 sm:-translate-x-4 z-10 w-8 h-8 rounded-full bg-zinc-800/80 hover:bg-zinc-700 flex items-center justify-center transition-colors text-zinc-400 hover:text-white"
          aria-label="Previous"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"></polyline>
          </svg>
        </button>

        <button
          onClick={handleNext}
          className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-2 sm:translate-x-4 z-10 w-8 h-8 rounded-full bg-zinc-800/80 hover:bg-zinc-700 flex items-center justify-center transition-colors text-zinc-400 hover:text-white"
          aria-label="Next"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="9 18 15 12 9 6"></polyline>
          </svg>
        </button>

        {/* Scrollable carousel */}
        <div
          ref={carouselRef}
          className="overflow-x-auto scrollbar-hide snap-x snap-mandatory scroll-smooth"
          style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
          onScroll={handleScroll}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseLeave}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
        >
          <div className="flex">
            {categories.map((cat) => {
              const config = categoryConfig[cat];
              // Handle old FFGA data format: map optimism to goals+aspirations fallback
              const sentimentAny = sentiment as unknown as Record<string, { summary: string } | undefined>;
              const categoryData = sentimentAny[cat] ||
                (cat === "optimism" && sentimentAny.goals ? sentimentAny.goals : null);
              const summary = categoryData?.summary || "No data available.";

              return (
                <div
                  key={cat}
                  className="w-full flex-shrink-0 snap-center px-2 sm:px-8"
                >
                  <div>
                    <h3 className="text-sm font-semibold text-zinc-300 mb-2 font-[family-name:var(--font-space-mono)]">
                      {config.label}
                    </h3>
                    <ul className="text-sm text-zinc-400 leading-relaxed space-y-2">
                      {summary
                        .split(/(?<=[.!?])\s+/)
                        .filter((sentence) => sentence.trim())
                        .map((sentence, idx) => (
                          <li key={idx} className="flex gap-2">
                            <span className="text-zinc-600 mt-0.5">•</span>
                            <span
                              dangerouslySetInnerHTML={{
                                __html: sentence
                                  // Bold words at start of sentence (first 2-4 words before a comma or colon)
                                  .replace(/^([^,.:]+[,.:]?)/, '<strong class="text-zinc-200">$1</strong>')
                              }}
                            />
                          </li>
                        ))}
                    </ul>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Dots navigation */}
      <div className="flex justify-center gap-2 mt-3">
        {categories.map((cat, index) => (
          <button
            key={cat}
            onClick={() => handleDotClick(index)}
            className={`w-2 h-2 rounded-full transition-all ${
              index === activeIndex
                ? "bg-zinc-300 w-4"
                : "bg-zinc-600 hover:bg-zinc-500"
            }`}
            aria-label={`Go to ${categoryConfig[cat].label}`}
          />
        ))}
      </div>
    </div>
  );
}