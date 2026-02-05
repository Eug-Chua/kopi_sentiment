"""Data models for sentiment analysis output"""

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

class Intensity(str, Enum):
    """How strongly the FFO emotion is expressed"""
    MILD = "mild"          # Slight, passing mention
    MODERATE = "moderate"  # Clear expression
    STRONG = "strong"      # Intense, emphatic expression


class FFOCategory(str, Enum):
    """FFO framework categories (Fears, Frustrations, Optimism)"""
    FEAR = "fear"
    FRUSTRATION = "frustration"
    OPTIMISM = "optimism"



class ExtractedQuote(BaseModel):
    """A quote extracted by the LLM with its comment score"""
    quote: str
    score: int = 0  # Comment upvote score


class FFOResult(BaseModel):
    """Result for a single FFO category"""
    category: FFOCategory
    intensity: Intensity
    summary: str
    quotes: list[ExtractedQuote] = []




class AnalysisResult(BaseModel):
    """Complete FFO analysis for a post"""
    post_id: str
    post_title: str
    fears: FFOResult
    frustrations: FFOResult
    optimism: FFOResult


# ============================================================================
# Weekly Report Models
# ============================================================================

class QuoteWithMetadata(BaseModel):
    """A quote with full context for UI display"""
    text: str
    post_id: str
    post_title: str
    subreddit: str
    score: int  # Post score (for backwards compatibility)
    comment_score: int = 0  # Comment upvote score
    intensity: Intensity


class IntensityBreakdown(BaseModel):
    """Count of quotes by intensity level"""
    mild: int = 0
    moderate: int = 0
    strong: int = 0


class CategorySummary(BaseModel):
    """Aggregated summary for one FFO category"""
    intensity: Intensity
    summary: str = Field(description="3-4 sentence LLM-generated summary")
    quote_count: int
    intensity_breakdown: IntensityBreakdown


class OverallSentiment(BaseModel):
    """Weekly sentiment across all subreddits"""
    fears: CategorySummary
    frustrations: CategorySummary
    optimism: CategorySummary


class PostAnalysis(BaseModel):
    """Analysis for a single post with metadata"""
    id: str
    title: str
    url: str
    score: int
    num_comments: int
    created_at: datetime
    subreddit: str
    analysis: AnalysisResult


class SubredditReport(BaseModel):
    """Weekly report for a single subreddit"""
    name: str
    posts_analyzed: int
    comments_analyzed: int
    top_posts: list[PostAnalysis]


class SamplePost(BaseModel):
    """A sample post with title and optional URL"""
    title: str
    url: str | None = None


class ThematicCluster(BaseModel):
    """A topic cluster representing what people are discussing, weighted by engagement"""
    topic: str = Field(description="Specific topic name (5-8 words)")
    engagement_score: int = Field(description="Sum of upvotes from posts discussing this topic")
    dominant_emotion: FFOCategory
    sample_posts: list[str | SamplePost] = Field(default=[], description="Representative post titles (max 3)")
    entities: list[str] = Field(default=[], description="Key entities for trend tracking (e.g., HDB, CPF, Employment)")


class WeeklyReportMetadata(BaseModel):
    """Metadata about the weekly report generation"""
    total_posts_analyzed: int
    total_comments_analyzed: int
    subreddits: list[str]


class AllQuotes(BaseModel):
    """All quotes organized by category"""
    fears: list[QuoteWithMetadata] = []
    frustrations: list[QuoteWithMetadata] = []
    optimism: list[QuoteWithMetadata] = []


# ============================================================================
# Enhanced Insights Models (v2)
# ============================================================================

class TrendDirection(str, Enum):
    """Direction of sentiment change week-over-week"""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class CategoryTrend(BaseModel):
    """Week-over-week trend for a single FFO category"""
    direction: TrendDirection
    change_pct: float = Field(description="Percentage change in quote count")
    intensity_shift: str = Field(description="e.g., 'mild → moderate' or 'stable'")
    previous_count: int
    current_count: int


class WeeklyTrends(BaseModel):
    """Trend data comparing current week to previous week"""
    has_previous_week: bool = False
    previous_week_id: str | None = None
    fears: CategoryTrend | None = None
    frustrations: CategoryTrend | None = None
    optimism: CategoryTrend | None = None


class ThemeCluster(BaseModel):
    """A cluster of related quotes around a common theme"""
    theme: str = Field(description="Short theme name, e.g., 'Housing Affordability'")
    description: str = Field(description="1-sentence description of the theme")
    category: FFOCategory
    quote_count: int
    sample_quotes: list[str] = Field(description="Representative quotes (max 3)")
    avg_score: float = Field(description="Average engagement score of quotes in cluster")


class SignalType(str, Enum):
    """Types of signals that warrant attention"""
    HIGH_ENGAGEMENT = "high_engagement"  # Unusually high upvotes
    EMERGING_TOPIC = "emerging_topic"    # New topic not seen before
    INTENSITY_SPIKE = "intensity_spike"  # Jump in strong emotions
    VOLUME_SPIKE = "volume_spike"        # Unusual number of mentions


class Signal(BaseModel):
    """A notable signal that warrants attention"""
    signal_type: SignalType
    title: str = Field(description="Short signal headline")
    description: str = Field(description="Why this signal matters")
    category: FFOCategory | None = None
    related_quotes: list[str] = []
    urgency: Literal["low", "medium", "high"] = "medium"


class WeeklyInsights(BaseModel):
    """AI-generated insights and recommendations"""
    headline: str = Field(description="One-line summary of the week's sentiment")
    key_takeaways: list[str] = Field(description="3-5 bullet points of notable findings")
    opportunities: list[str] = Field(description="Actionable opportunities identified")
    risks: list[str] = Field(description="Potential risks or concerns to monitor")


class WeeklyReport(BaseModel):
    """Complete weekly sentiment report - main output format"""
    schema_version: str = "weekly_report_v2"
    week_id: str = Field(description="ISO week format, e.g., '2025-W02'")
    week_start: date
    week_end: date
    generated_at: datetime

    metadata: WeeklyReportMetadata
    overall_sentiment: OverallSentiment
    subreddits: list[SubredditReport]
    all_quotes: AllQuotes
    thematic_clusters: list[ThematicCluster] = []

    # Enhanced insights
    insights: WeeklyInsights | None = None
    trends: WeeklyTrends | None = None
    theme_clusters: list[ThemeCluster] = []  # Quote-based clusters (different from thematic_clusters)
    signals: list[Signal] = []


# ============================================================================
# Daily Report Models
# ============================================================================

class DailyReportMetadata(BaseModel):
    """Metadata about the daily report generation"""
    total_posts_analyzed: int
    total_comments_analyzed: int
    subreddits: list[str]


class DailyTrends(BaseModel):
    """Trend data comparing current day to previous day"""
    has_previous_day: bool = False
    previous_date: date | None = None
    fears: CategoryTrend | None = None
    frustrations: CategoryTrend | None = None
    optimism: CategoryTrend | None = None


class DailyInsights(BaseModel):
    """AI-generated insights for a single day"""
    headline: str = Field(description="One-line summary of the day's sentiment")
    key_takeaways: list[str] = Field(description="3-5 bullet points of notable findings")
    opportunities: list[str] = Field(description="Actionable opportunities identified")
    risks: list[str] = Field(description="Potential risks or concerns to monitor")


class DailyReport(BaseModel):
    """Complete daily sentiment report"""
    schema_version: str = "daily_report_v1"
    date_id: str = Field(description="Date format, e.g., '2025-01-15'")
    report_date: date
    generated_at: datetime

    metadata: DailyReportMetadata
    overall_sentiment: OverallSentiment
    subreddits: list[SubredditReport]
    all_quotes: AllQuotes
    thematic_clusters: list[ThematicCluster] = []

    # Insights
    insights: DailyInsights | None = None
    trends: DailyTrends | None = None
    theme_clusters: list[ThemeCluster] = []  # Quote-based clusters (different from thematic_clusters)
    signals: list[Signal] = []