"use client";

import { useState, useEffect } from "react";
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

const QUOTES_PER_PAGE = 10;

export function CategoryTabs({ quotes, filter }: CategoryTabsProps) {
  const [activeTab, setActiveTab] = useState<string>("fears");
  const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>({
    fears: QUOTES_PER_PAGE,
    frustrations: QUOTES_PER_PAGE,
    goals: QUOTES_PER_PAGE,
    aspirations: QUOTES_PER_PAGE,
  });

  // When filter changes, switch to the filtered category tab
  useEffect(() => {
    if (filter) {
      setActiveTab(filter.category);
    }
  }, [filter]);

  // Sort quotes by score (highest first)
  const sortByScore = (quoteList: QuoteWithMetadata[]) => {
    return [...quoteList].sort((a, b) => b.score - a.score);
  };

  // Filter quotes by intensity if filter is active
  const filterQuotes = (quoteList: QuoteWithMetadata[], categoryKey: string) => {
    let filtered = sortByScore(quoteList);
    if (filter && filter.category === categoryKey && filter.intensity) {
      filtered = filtered.filter((q) => q.intensity === filter.intensity);
    }
    return filtered;
  };

  const categories = [
    { key: "fears", label: "Fears", data: quotes.fears },
    { key: "frustrations", label: "Frustrations", data: quotes.frustrations },
    { key: "goals", label: "Goals", data: quotes.goals },
    { key: "aspirations", label: "Aspirations", data: quotes.aspirations },
  ];

  const handleLoadMore = (categoryKey: string) => {
    setVisibleCounts((prev) => ({
      ...prev,
      [categoryKey]: prev[categoryKey] + QUOTES_PER_PAGE,
    }));
  };

  return (
    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        {categories.map((cat) => {
          const filteredData = filterQuotes(cat.data, cat.key);
          const isFiltered = filter && filter.category === cat.key;
          return (
            <TabsTrigger key={cat.key} value={cat.key}>
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
              {visibleQuotes.length === 0 ? (
                <div className="text-center text-zinc-500 py-8">
                  No quotes found for this filter
                </div>
              ) : (
                visibleQuotes.map((quote, idx) => (
                  <QuoteCard key={idx} quote={quote} />
                ))
              )}
              {hasMore && (
                <button
                  onClick={() => handleLoadMore(cat.key)}
                  className="w-full py-3 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                >
                  Load more comments ({filteredData.length - visibleCounts[cat.key]} remaining)
                </button>
              )}
            </div>
          </TabsContent>
        );
      })}
    </Tabs>
  );
}