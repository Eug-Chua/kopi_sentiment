"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { QuoteCard } from "./QuoteCard";
import { AllQuotes, QuoteWithMetadata } from "@/types";

interface CategoryTabsProps {
  quotes: AllQuotes;
}

const QUOTES_PER_PAGE = 10;

export function CategoryTabs({ quotes }: CategoryTabsProps) {
  const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>({
    fears: QUOTES_PER_PAGE,
    frustrations: QUOTES_PER_PAGE,
    goals: QUOTES_PER_PAGE,
    aspirations: QUOTES_PER_PAGE,
  });

  // Sort quotes by score (highest first)
  const sortByScore = (quoteList: QuoteWithMetadata[]) => {
    return [...quoteList].sort((a, b) => b.score - a.score);
  };

  const categories = [
    { key: "fears", label: "Fears", data: sortByScore(quotes.fears) },
    { key: "frustrations", label: "Frustrations", data: sortByScore(quotes.frustrations) },
    { key: "goals", label: "Goals", data: sortByScore(quotes.goals) },
    { key: "aspirations", label: "Aspirations", data: sortByScore(quotes.aspirations) },
  ];

  const handleLoadMore = (categoryKey: string) => {
    setVisibleCounts((prev) => ({
      ...prev,
      [categoryKey]: prev[categoryKey] + QUOTES_PER_PAGE,
    }));
  };

  return (
    <Tabs defaultValue="fears" className="w-full">
      <TabsList className="grid w-full grid-cols-4">
        {categories.map((cat) => (
          <TabsTrigger key={cat.key} value={cat.key}>
            {cat.label} ({cat.data.length})
          </TabsTrigger>
        ))}
      </TabsList>
      {categories.map((cat) => {
        const visibleQuotes = cat.data.slice(0, visibleCounts[cat.key]);
        const hasMore = visibleCounts[cat.key] < cat.data.length;

        return (
          <TabsContent key={cat.key} value={cat.key}>
            <div className="space-y-3 mt-4">
              {visibleQuotes.map((quote, idx) => (
                <QuoteCard key={idx} quote={quote} />
              ))}
              {hasMore && (
                <button
                  onClick={() => handleLoadMore(cat.key)}
                  className="w-full py-3 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                >
                  Load more comments ({cat.data.length - visibleCounts[cat.key]} remaining)
                </button>
              )}
            </div>
          </TabsContent>
        );
      })}
    </Tabs>
  );
}