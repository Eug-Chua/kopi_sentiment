"""Data models for sentiment analysis output"""

from datetime import date, datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

class Intensity(str, Enum):
    """How strongly the FFGA emotion is expressed"""
    MILD = "mild"          # Slight, passing mention
    MODERATE = "moderate"  # Clear expression
    STRONG = "strong"      # Intense, emphatic expression

class FFGACategory(str, Enum):
    """FFGA framework categories"""
    FEAR = "fear"
    FRUSTRATION = "frustration"
    GOAL = "goal"
    ASPIRATION = "aspiration"

class FFGAResult(BaseModel):
    """Result for a single FFGA category"""
    category: FFGACategory
    intensity: Intensity
    summary: str
    quotes: list[str] = []

class AnalysisResult(BaseModel):
    """Complete FFGA analysis for a post"""
    post_id: str
    post_title: str
    fears: FFGAResult
    frustrations: FFGAResult
    goals: FFGAResult
    aspirations: FFGAResult


# ============================================================================
# Weekly Report Models
# ============================================================================

class QuoteWithMetadata(BaseModel):
    """A quote with full context for UI display"""
    text: str
    post_id: str
    post_title: str
    subreddit: str
    score: int
    intensity: Intensity


class IntensityBreakdown(BaseModel):
    """Count of quotes by intensity level"""
    mild: int = 0
    moderate: int = 0
    strong: int = 0


class CategorySummary(BaseModel):
    """Aggregated summary for one FFGA category"""
    intensity: Intensity
    summary: str = Field(description="2-sentence LLM-generated summary")
    quote_count: int
    intensity_breakdown: IntensityBreakdown


class OverallSentiment(BaseModel):
    """Weekly sentiment across all subreddits"""
    fears: CategorySummary
    frustrations: CategorySummary
    goals: CategorySummary
    aspirations: CategorySummary


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


class TrendingTopic(BaseModel):
    """Detected trending topic with sentiment"""
    topic: str
    mentions: int
    dominant_emotion: FFGACategory
    sentiment_shift: Literal["improving", "stable", "worsening"]


class WeeklyReportMetadata(BaseModel):
    """Metadata about the weekly report generation"""
    total_posts_analyzed: int
    total_comments_analyzed: int
    subreddits: list[str]


class AllQuotes(BaseModel):
    """All quotes organized by category"""
    fears: list[QuoteWithMetadata] = []
    frustrations: list[QuoteWithMetadata] = []
    goals: list[QuoteWithMetadata] = []
    aspirations: list[QuoteWithMetadata] = []


class WeeklyReport(BaseModel):
    """Complete weekly sentiment report - main output format"""
    schema_version: str = "weekly_report_v1"
    week_id: str = Field(description="ISO week format, e.g., '2025-W02'")
    week_start: date
    week_end: date
    generated_at: datetime

    metadata: WeeklyReportMetadata
    overall_sentiment: OverallSentiment
    subreddits: list[SubredditReport]
    all_quotes: AllQuotes
    trending_topics: list[TrendingTopic] = []