"use client";

import { TrendingTopic, FFGACategory } from "@/types";

interface TrendingThemesComparisonProps {
  currentTopics: TrendingTopic[];
  previousTopics: TrendingTopic[];
  currentLabel: string;
  previousLabel: string;
}

function getCategoryColor(category: FFGACategory): string {
  switch (category) {
    case "fear": return "bg-purple-500/20 text-purple-400 border-purple-500/30";
    case "frustration": return "bg-red-500/20 text-red-400 border-red-500/30";
    case "goal": return "bg-blue-500/20 text-blue-400 border-blue-500/30";
    case "aspiration": return "bg-green-500/20 text-green-400 border-green-500/30";
    default: return "bg-zinc-500/20 text-zinc-400 border-zinc-500/30";
  }
}

function getSentimentIcon(shift: string): string {
  switch (shift) {
    case "improving": return "↗";
    case "worsening": return "↘";
    default: return "→";
  }
}

function getSentimentColor(shift: string): string {
  switch (shift) {
    case "improving": return "text-green-400";
    case "worsening": return "text-red-400";
    default: return "text-zinc-500";
  }
}

function TopicList({ topics, emptyMessage }: { topics: TrendingTopic[]; emptyMessage: string }) {
  if (!topics || topics.length === 0) {
    return (
      <div className="text-sm text-zinc-500 italic">{emptyMessage}</div>
    );
  }

  return (
    <div className="space-y-2">
      {topics.slice(0, 5).map((topic, i) => (
        <div key={i} className="flex items-start gap-2">
          <span className="text-zinc-600 text-sm font-medium w-4 flex-shrink-0">{i + 1}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-sm text-white font-medium truncate" title={topic.topic}>
                {topic.topic}
              </span>
              <span className={`text-xs flex-shrink-0 ${getSentimentColor(topic.sentiment_shift)}`}>
                {getSentimentIcon(topic.sentiment_shift)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`text-xs px-1.5 py-0.5 rounded border ${getCategoryColor(topic.dominant_emotion)}`}>
                {topic.dominant_emotion}
              </span>
              <span className="text-xs text-zinc-500">{topic.mentions}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function TrendingThemesComparison({
  currentTopics,
  previousTopics,
  currentLabel,
  previousLabel
}: TrendingThemesComparisonProps) {
  // Find new topics (in current but not in previous)
  const previousTopicNames = new Set(previousTopics.map(t => t.topic.toLowerCase()));
  const newTopics = currentTopics.filter(t => !previousTopicNames.has(t.topic.toLowerCase()));

  // Find topics that dropped off (in previous but not in current)
  const currentTopicNames = new Set(currentTopics.map(t => t.topic.toLowerCase()));
  const droppedTopics = previousTopics.filter(t => !currentTopicNames.has(t.topic.toLowerCase()));

  return (
    <div className="bg-zinc-900/50 rounded-lg p-4 border border-zinc-800">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Current Period */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-medium text-white">{currentLabel}</h3>
            {newTopics.length > 0 && (
              <span className="text-xs px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">
                {newTopics.length} new
              </span>
            )}
          </div>
          <TopicList topics={currentTopics} emptyMessage="No trending topics" />
        </div>

        {/* Previous Period */}
        <div className="md:border-l md:border-zinc-800 md:pl-6">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-sm font-medium text-zinc-400">{previousLabel}</h3>
          </div>
          <TopicList topics={previousTopics} emptyMessage="No previous data" />
        </div>
      </div>
    </div>
  );
}