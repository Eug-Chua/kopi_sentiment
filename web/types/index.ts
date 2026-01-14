// Types that mirror Python Pydantic models

export type Intensity = "low" | "medium" | "high";

export type FFGACategory = "fears" | "frustrations" | "goals" | "aspirations";

export interface QuoteWithMetadata {
  text: string;
  post_id: string;
  post_title: string;
  subreddit: string;
  score: number;
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

export interface TrendingTopic {
  topic: string;
  mention_count: number;
  related_quotes: string[];
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

export interface WeeklyReport {
  week_id: string;
  week_start: string;
  week_end: string;
  generated_at: string;
  metadata: WeeklyReportMetadata;
  overall_sentiment: OverallSentiment;
  subreddits: SubredditReport[];
  all_quotes: AllQuotes;
  trending_topics: TrendingTopic[];
}
