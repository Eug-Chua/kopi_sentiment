// Types that mirror Python Pydantic models

export type Intensity = "mild" | "moderate" | "strong";

export type FFOCategory = "fear" | "frustration" | "optimism";

export interface QuoteWithMetadata {
  text: string;
  post_id: string;
  post_title: string;
  subreddit: string;
  score: number;  // Post score (for backwards compatibility)
  comment_score?: number;  // Comment upvote score
  intensity: Intensity;
}

export interface FFOResult {
  category: FFOCategory;
  quotes: string[];
  intensity: Intensity;
}

export interface AnalysisResult {
  fears: FFOResult;
  frustrations: FFOResult;
  optimism: FFOResult;
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
  optimism: QuoteWithMetadata[];
}

export interface SamplePost {
  title: string;
  url: string | null;
}

export interface ThematicCluster {
  topic: string;
  engagement_score: number;  // Sum of upvotes from related posts
  dominant_emotion: FFOCategory;
  sample_posts: (string | SamplePost)[];  // Representative post titles (max 3)
  entities?: string[];  // Key entities for trend tracking (e.g., HDB, CPF, Employment)
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
    optimism: CategorySentiment;
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
  optimism: CategoryTrend | null;
}

export interface ThemeCluster {
  theme: string;
  description: string;
  category: FFOCategory;
  quote_count: number;
  sample_quotes: string[];
  avg_score: number;
}

export type SignalType = "high_engagement" | "emerging_topic" | "intensity_spike" | "volume_spike";

export interface Signal {
  signal_type: SignalType;
  title: string;
  description: string;
  category: FFOCategory | null;
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
  optimism: CategoryTrend | null;
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

// ============================================================================
// Analytics Types (for trend analysis and data science features)
// ============================================================================

export type AnalyticsTrendDirection = "rising" | "falling" | "stable";
export type AlertSeverity = "none" | "notable" | "warning" | "alert";
export type TrendStrength = "weak" | "moderate" | "strong";

export interface DailySentimentScore {
  date: string;
  fears_count: number;
  frustrations_count: number;
  optimism_count: number;
  total_quotes: number;
  fears_zscore_sum: number;
  frustrations_zscore_sum: number;
  optimism_zscore_sum: number;
  // Dual sentiment scores
  negativity_score: number;  // fears + frustrations z-score sum
  positivity_score: number;  // optimism z-score sum
  composite_score: number;
  ema_score: number | null;
  ema_negativity: number | null;
  ema_positivity: number | null;
  total_engagement: number;
  avg_engagement: number;
}

export interface SentimentTimeSeries {
  start_date: string;
  end_date: string;
  data_points: DailySentimentScore[];
  mean_score: number;
  std_dev: number;
  min_score: number;
  max_score: number;
  overall_trend: AnalyticsTrendDirection;
  trend_slope: number;
  trend_r_squared: number;
}

export interface CategoryMomentum {
  category: "fears" | "frustrations" | "optimism";
  current_count: number;
  current_zscore_sum: number;
  roc_1d: number;
  roc_3d: number;
  roc_7d: number;
  ema_momentum: number;
  trend: AnalyticsTrendDirection;
  trend_strength: TrendStrength;
}

export interface MomentumReport {
  report_date: string;
  lookback_days: number;
  fears: CategoryMomentum;
  frustrations: CategoryMomentum;
  optimism: CategoryMomentum;
  fastest_rising: string;
  fastest_falling: string;
}

export interface VelocityMetric {
  metric_name: string;
  current_value: number;
  velocity: number;
  velocity_zscore: number;
  acceleration: number;
  historical_mean: number;
  historical_std: number;
  alert_level: AlertSeverity;
}

export interface TrendVelocityAlert {
  alert_id: string;
  triggered_at: string;
  severity: AlertSeverity;
  metric: string;
  category: string | null;
  current_value: number;
  expected_value: number;
  z_score: number;
  percentile: number;
  direction: AnalyticsTrendDirection;
  description: string;
  top_quotes: string[];
}

export interface VelocityReport {
  report_date: string;
  lookback_days: number;
  metrics: VelocityMetric[];
  alerts: TrendVelocityAlert[];
  total_alerts: number;
  alert_count: number;
  warning_count: number;
}

export interface AnalyticsReport {
  schema_version: string;
  generated_at: string;
  data_range_start: string;
  data_range_end: string;
  days_analyzed: number;
  sentiment_timeseries: SentimentTimeSeries;
  momentum: MomentumReport;
  velocity: VelocityReport;
  headline: string;
  key_insights: string[];
  sentiment_commentary: string;  // LLM-generated plain-language explanation of sentiment scores
  methodology: string;
  entity_trends: EntityTrendsReport | null;
}

// ============================================================================
// Entity Trends Types
// ============================================================================

export interface EntityDayData {
  date: string;
  engagement: number;
  mention_count: number;
  categories: string[];
}

export interface EntityTrend {
  entity: string;
  total_engagement: number;
  total_mentions: number;
  days_present: number;
  daily_data: EntityDayData[];
  dominant_category: string;
  trend_direction: "rising" | "falling" | "stable";
}

export interface EntityTrendsReport {
  generated_at: string;
  days_analyzed: number;
  top_entities: EntityTrend[];
}

