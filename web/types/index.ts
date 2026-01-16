// Types that mirror Python Pydantic models

export type Intensity = "mild" | "moderate" | "strong";

export type FFGACategory = "fear" | "frustration" | "goal" | "aspiration";

export interface QuoteWithMetadata {
  text: string;
  post_id: string;
  post_title: string;
  subreddit: string;
  score: number;  // Post score (for backwards compatibility)
  comment_score?: number;  // Comment upvote score
  intensity: Intensity;
}

export interface FFGAResult {
  category: FFGACategory;
  quotes: string[];
  intensity: Intensity;
}

export interface AnalysisResult {
  fears: FFGAResult;
  frustrations: FFGAResult;
  goals: FFGAResult;
  aspirations: FFGAResult;
}

export interface PostAnalysis {
  id: string;
  title: string;
  url: string;
  score: number;
  num_comments: number;
  created_at: string;
  subreddit: string;
  analysis: AnalysisResult;
}

export interface SubredditReport {
  name: string;
  posts_analyzed: number;
  comments_analyzed: number;
  top_posts: PostAnalysis[];
}

export interface AllQuotes {
  fears: QuoteWithMetadata[];
  frustrations: QuoteWithMetadata[];
  goals: QuoteWithMetadata[];
  aspirations: QuoteWithMetadata[];
}

export interface ThematicCluster {
  topic: string;
  engagement_score: number;  // Sum of upvotes from related posts
  dominant_emotion: FFGACategory;
  sample_posts: string[];  // Representative post titles (max 3)
}

export interface CategorySentiment {
    intensity: string;
    summary: string;
    quote_count: number;
    intensity_breakdown: {
      mild: number;
      moderate: number;
      strong: number;
    };
  }
  
  export interface OverallSentiment {
    fears: CategorySentiment;
    frustrations: CategorySentiment;
    goals: CategorySentiment;
    aspirations: CategorySentiment;
  }

export interface WeeklyReportMetadata {
  total_posts_analyzed: number;
  total_comments_analyzed: number;
  subreddits: string[];
}

// ============================================================================
// Enhanced Insights Types (v2)
// ============================================================================

export type TrendDirection = "up" | "down" | "stable";

export interface CategoryTrend {
  direction: TrendDirection;
  change_pct: number;
  intensity_shift: string;
  previous_count: number;
  current_count: number;
}

export interface WeeklyTrends {
  has_previous_week: boolean;
  previous_week_id: string | null;
  fears: CategoryTrend | null;
  frustrations: CategoryTrend | null;
  goals: CategoryTrend | null;
  aspirations: CategoryTrend | null;
}

export interface ThemeCluster {
  theme: string;
  description: string;
  category: FFGACategory;
  quote_count: number;
  sample_quotes: string[];
  avg_score: number;
}

export type SignalType = "high_engagement" | "emerging_topic" | "intensity_spike" | "volume_spike";

export interface Signal {
  signal_type: SignalType;
  title: string;
  description: string;
  category: FFGACategory | null;
  related_quotes: string[];
  urgency: "low" | "medium" | "high";
}

export interface WeeklyInsights {
  headline: string;
  key_takeaways: string[];
  opportunities: string[];
  risks: string[];
}

export interface WeeklyReport {
  schema_version?: string;
  week_id: string;
  week_start: string;
  week_end: string;
  generated_at: string;
  metadata: WeeklyReportMetadata;
  overall_sentiment: OverallSentiment;
  subreddits: SubredditReport[];
  all_quotes: AllQuotes;
  thematic_clusters?: ThematicCluster[];
  // Enhanced insights
  insights: WeeklyInsights | null;
  trends: WeeklyTrends | null;
  theme_clusters: ThemeCluster[];
  signals: Signal[];
}

// ============================================================================
// Daily Report Types
// ============================================================================

export interface DailyReportMetadata {
  total_posts_analyzed: number;
  total_comments_analyzed: number;
  subreddits: string[];
}

export interface DailyTrends {
  has_previous_day: boolean;
  previous_date: string | null;
  fears: CategoryTrend | null;
  frustrations: CategoryTrend | null;
  goals: CategoryTrend | null;
  aspirations: CategoryTrend | null;
}

export interface DailyInsights {
  headline: string;
  key_takeaways: string[];
  opportunities: string[];
  risks: string[];
}

export interface DailyReport {
  schema_version?: string;
  date_id: string;
  report_date: string;
  generated_at: string;
  metadata: DailyReportMetadata;
  overall_sentiment: OverallSentiment;
  subreddits: SubredditReport[];
  all_quotes: AllQuotes;
  thematic_clusters?: ThematicCluster[];
  // Insights
  insights: DailyInsights | null;
  trends: DailyTrends | null;
  theme_clusters: ThemeCluster[];
  signals: Signal[];
}

// Union type for either report type
export type Report = WeeklyReport | DailyReport;
export type ReportMode = "daily" | "weekly";
