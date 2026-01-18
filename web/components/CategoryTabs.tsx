"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { QuoteCard } from "./QuoteCard";
import { AllQuotes, QuoteWithMetadata, Intensity } from "@/types";

type CategoryKey = "fears" | "frustrations" | "goals" | "aspirations";

export interface QuoteFilter {
  category: CategoryKey;
  intensity?: Intensity; // Optional - if undefined, show all intensities for category
}

interface CategoryTabsProps {
  quotes: AllQuotes;
  filter?: QuoteFilter | null;
}

const QUOTES_PER_PAGE = 5;

function InfiniteScrollTrigger({ onIntersect, hasMore, isLoading }: { onIntersect: () => void; hasMore: boolean; isLoading: boolean }) {
  const triggerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasMore || isLoading) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          onIntersect();
        }
      },
      { threshold: 0.1 }
    );

    if (triggerRef.current) {
      observer.observe(triggerRef.current);
    }

    return () => observer.disconnect();
  }, [onIntersect, hasMore, isLoading]);

  if (!hasMore) return null;

  return (
    <div ref={triggerRef} className="py-4 text-center">
      {isLoading ? (
        <span className="text-sm text-zinc-400 animate-pulse">Loading more...</span>
      ) : (
        <span className="text-sm text-zinc-600">Scroll for more</span>
      )}
    </div>
  );
}

export function CategoryTabs({ quotes, filter }: CategoryTabsProps) {
  const [activeTab, setActiveTab] = useState<string>("fears");
  const [searchQuery, setSearchQuery] = useState("");
  const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>({
    fears: QUOTES_PER_PAGE,
    frustrations: QUOTES_PER_PAGE,
    goals: QUOTES_PER_PAGE,
    aspirations: QUOTES_PER_PAGE,
  });
  const [loadingCategory, setLoadingCategory] = useState<string | null>(null);

  // When filter changes, switch to the filtered category tab
  useEffect(() => {
    if (filter) {
      setActiveTab(filter.category);
    }
  }, [filter]);

  // Sort quotes by score (highest first), preferring comment_score when present
  const sortByScore = (quoteList: QuoteWithMetadata[]) => {
    return [...quoteList].sort((a, b) => {
      const scoreA = a.comment_score ?? a.score;
      const scoreB = b.comment_score ?? b.score;
      return scoreB - scoreA;
    });
  };

  // Filter quotes by intensity if filter is active
  const filterQuotes = (quoteList: QuoteWithMetadata[], categoryKey: string) => {
    let filtered = sortByScore(quoteList);
    if (filter && filter.category === categoryKey && filter.intensity) {
      filtered = filtered.filter((q) => q.intensity === filter.intensity);
    }
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((q) => 
        q.text.toLowerCase().includes(query) || 
        q.post_title.toLowerCase().includes(query)
      );
    }
    return filtered;
  };
  

  const categories = [
    { key: "fears", label: "Fears", data: quotes.fears },
    { key: "frustrations", label: "Frustrations", data: quotes.frustrations },
    { key: "goals", label: "Goals", data: quotes.goals },
    { key: "aspirations", label: "Aspirations", data: quotes.aspirations },
  ];

  const handleLoadMore = useCallback((categoryKey: string) => {
    setLoadingCategory(categoryKey);
    // Add small delay for loading feel
    setTimeout(() => {
      setVisibleCounts((prev) => ({
        ...prev,
        [categoryKey]: prev[categoryKey] + QUOTES_PER_PAGE,
      }));
      setLoadingCategory(null);
    }, 400);
  }, []);

  return (
    <>
      <div className="mb-4">
        <input
          type="text"
          placeholder="Search quotes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 bg-zinc-800/50 border border-zinc-700 rounded-lg text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-600"
        />
      </div>
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 h-auto gap-1">
        {categories.map((cat) => {
          const filteredData = filterQuotes(cat.data, cat.key);
          const isFiltered = filter && filter.category === cat.key;
          return (
            <TabsTrigger key={cat.key} value={cat.key} className="text-xs sm:text-sm py-2">
              {cat.label} ({isFiltered ? filteredData.length : cat.data.length})
            </TabsTrigger>
          );
        })}
      </TabsList>
      {categories.map((cat) => {
        const filteredData = filterQuotes(cat.data, cat.key);
        const visibleQuotes = filteredData.slice(0, visibleCounts[cat.key]);
        const hasMore = visibleCounts[cat.key] < filteredData.length;

        return (
          <TabsContent key={cat.key} value={cat.key}>
            <div className="space-y-3 mt-4">
              {/* Progress indicator */}
              {filteredData.length > 0 && (
                <div className="text-xs text-zinc-500 text-center pb-2">
                  Showing {Math.min(visibleCounts[cat.key], filteredData.length)} of {filteredData.length} quotes
                </div>
              )}
              {visibleQuotes.length === 0 ? (
                <div className="text-center text-zinc-500 py-8">
                  No quotes found for this filter
                </div>
              ) : (
                visibleQuotes.map((quote, idx) => (
                  <QuoteCard key={idx} quote={quote} />
                ))
              )}
              <InfiniteScrollTrigger
                onIntersect={() => handleLoadMore(cat.key)}
                hasMore={hasMore}
                isLoading={loadingCategory === cat.key}
              />
            </div>
          </TabsContent>
        );
      })}
    </Tabs>
    </>
  );
}