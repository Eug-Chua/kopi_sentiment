"""Base pipeline with shared logic for daily and weekly pipelines."""

from abc import ABC, abstractmethod
from datetime import datetime
import logging

from kopi_sentiment.scraper.reddit import RedditScraper, RedditPost
from kopi_sentiment.config.settings import settings
from kopi_sentiment.analyzer.base import BaseAnalyzer, create_analyzer
from kopi_sentiment.analyzer.models import (
    SubredditReport,
    AnalysisResult,
    AllQuotes,
    PostAnalysis,
    QuoteWithMetadata,
    CategoryTrend,
    TrendDirection,
)

logger = logging.getLogger(__name__)


class BasePipeline(ABC):
    """Abstract base class for sentiment analysis pipelines."""

    def __init__(
        self,
        subreddits: list[str] | None,
        posts_per_subreddit: int,
        llm_provider: str | None,
    ):
        """Initialize shared pipeline config."""
        self.subreddits = subreddits or settings.reddit_subreddit
        self.posts_per_subreddit = posts_per_subreddit
        self.analyzer = create_analyzer(llm_provider)

    # -------------------------------------------------------------------------
    # Abstract methods - subclasses must implement
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_report_id(self, target_date=None) -> str:
        """Get the report ID (week_id or date_id)."""
        pass

    @abstractmethod
    def scrape_subreddit(self, subreddit: str) -> list[RedditPost]:
        """Scrape posts from a subreddit with appropriate time filter."""
        pass

    @abstractmethod
    def run(self, report_id: str | None = None):
        """Execute the full pipeline."""
        pass

    # -------------------------------------------------------------------------
    # Shared methods - identical in both pipelines
    # -------------------------------------------------------------------------

    def analyze_subreddit(
        self, subreddit: str, posts: list[RedditPost]
    ) -> tuple[SubredditReport, list[AnalysisResult]]:
        """Analyze all posts from a subreddit using 2-step LLM chain."""
        logger.info(f"Analyzing {len(posts)} posts from r/{subreddit}...")

        analyses = []
        post_analyses = []
        total_comments = 0

        for post in posts:
            try:
                analysis = self.analyzer.analyze(post)
                analyses.append(analysis)

                post_analysis = PostAnalysis(
                    id=post.id,
                    title=post.title,
                    url=post.url,
                    score=post.score,
                    num_comments=post.num_comments,
                    created_at=post.created_at,
                    subreddit=subreddit,
                    analysis=analysis,
                )
                post_analyses.append(post_analysis)
                total_comments += len(post.comments)
            except Exception as e:
                logger.error(f"Failed to analyze post {post.id}: {e}")
                continue

        report = SubredditReport(
            name=subreddit,
            posts_analyzed=len(post_analyses),
            comments_analyzed=total_comments,
            top_posts=post_analyses,
        )

        logger.info(f"Completed r/{subreddit}: {len(post_analyses)} posts, {total_comments} comments")
        return report, analyses

    def aggregate_quotes(self, subreddit_reports: list[SubredditReport]) -> AllQuotes:
        """Extract quotes from all analyses into QuoteWithMetadata."""
        all_quotes = AllQuotes()
        for report in subreddit_reports:
            for post_analysis in report.top_posts:
                analysis = post_analysis.analysis

                self._add_quotes(post_analysis, report, analysis.fears, all_quotes.fears)
                self._add_quotes(post_analysis, report, analysis.frustrations, all_quotes.frustrations)
                self._add_quotes(post_analysis, report, analysis.goals, all_quotes.goals)
                self._add_quotes(post_analysis, report, analysis.aspirations, all_quotes.aspirations)

        logger.info(
            f"Aggregated quotes: {len(all_quotes.fears)} fears, "
            f"{len(all_quotes.frustrations)} frustrations, "
            f"{len(all_quotes.goals)} goals, "
            f"{len(all_quotes.aspirations)} aspirations"
        )
        return all_quotes

    def _add_quotes(self, post_analysis, report, category_result, target_list):
        """Helper function to add quotes with metadata."""
        for extracted_quote in category_result.quotes:
            quote = QuoteWithMetadata(
                text=extracted_quote.quote,
                post_id=post_analysis.id,
                post_title=post_analysis.title,
                subreddit=report.name,
                score=post_analysis.score,
                comment_score=extracted_quote.score,
                intensity=category_result.intensity,
            )
            target_list.append(quote)

    def _count_intensity(self, all_analyses: list[AnalysisResult]) -> dict[str, dict[str, int]]:
        """Count quotes by intensity for each category."""
        counts = {
            "fears": {"mild": 0, "moderate": 0, "strong": 0},
            "frustrations": {"mild": 0, "moderate": 0, "strong": 0},
            "goals": {"mild": 0, "moderate": 0, "strong": 0},
            "aspirations": {"mild": 0, "moderate": 0, "strong": 0},
        }
        for analysis in all_analyses:
            for key, result in [
                ("fears", analysis.fears),
                ("frustrations", analysis.frustrations),
                ("goals", analysis.goals),
                ("aspirations", analysis.aspirations),
            ]:
                intensity = result.intensity.value if hasattr(result.intensity, "value") else result.intensity
                if intensity in counts[key]:
                    counts[key][intensity] += len(result.quotes)
        return counts

    def _get_high_engagement_quotes(
        self, all_quotes: AllQuotes, min_score: int = 10, limit: int = 10
    ) -> list[str]:
        """Get quotes with high engagement scores."""
        all_quote_list = (
            list(all_quotes.fears)
            + list(all_quotes.frustrations)
            + list(all_quotes.goals)
            + list(all_quotes.aspirations)
        )
        high_engagement = [q for q in all_quote_list if q.score >= min_score]
        high_engagement.sort(key=lambda q: q.score, reverse=True)
        return [f"[+{q.score}] {q.text}" for q in high_engagement[:limit]]

    def _calc_category_trend(self, current_count: int, previous_count: int) -> CategoryTrend:
        """Calculate trend for a single category."""
        if previous_count == 0:
            change_pct = 100.0 if current_count > 0 else 0.0
        else:
            change_pct = ((current_count - previous_count) / previous_count) * 100

        if change_pct > 10:
            direction = TrendDirection.UP
        elif change_pct < -10:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.STABLE

        return CategoryTrend(
            direction=direction,
            change_pct=round(change_pct, 1),
            intensity_shift="stable",
            previous_count=previous_count,
            current_count=current_count,
        )

    def quotes_to_dict(self, all_quotes: AllQuotes) -> dict[str, list[str]]:
        """Convert AllQuotes to dict format for LLM prompts."""
        return {
            "fears": [q.text for q in all_quotes.fears],
            "frustrations": [q.text for q in all_quotes.frustrations],
            "goals": [q.text for q in all_quotes.goals],
            "aspirations": [q.text for q in all_quotes.aspirations],
        }

    def get_post_titles_with_scores(self, subreddit_reports: list[SubredditReport]) -> list[str]:
        """Get post titles with scores for thematic clustering."""
        return [
            f"[+{post.score}] {post.title}"
            for report in subreddit_reports
            for post in report.top_posts
        ]
