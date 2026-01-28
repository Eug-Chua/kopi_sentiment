"""Base pipeline with shared logic for daily and weekly pipelines."""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    ThematicCluster,
    SamplePost,
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

    def _analyze_single_post(
        self, post: RedditPost, subreddit: str
    ) -> tuple[PostAnalysis, AnalysisResult] | None:
        """Analyze a single post. Used for parallel processing."""
        try:
            analysis = self.analyzer.analyze(post)
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
            return post_analysis, analysis
        except Exception as e:
            logger.error(f"Failed to analyze post {post.id}: {e}")
            return None

    def analyze_subreddit(
        self, subreddit: str, posts: list[RedditPost]
    ) -> tuple[SubredditReport, list[AnalysisResult]]:
        """Analyze all posts from a subreddit using parallel LLM calls."""
        max_workers = settings.analysis_max_workers
        logger.info(f"Analyzing {len(posts)} posts from r/{subreddit} ({max_workers} parallel workers)...")

        analyses = []
        post_analyses = []
        total_comments = 0

        # Process posts in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all posts to the thread pool
            future_to_post = {
                executor.submit(self._analyze_single_post, post, subreddit): post
                for post in posts
            }

            # Collect results as they complete
            for future in as_completed(future_to_post):
                post = future_to_post[future]
                result = future.result()

                if result is not None:
                    post_analysis, analysis = result
                    post_analyses.append(post_analysis)
                    analyses.append(analysis)
                    total_comments += len(post.comments)

        # Sort by original order (post score descending) to maintain consistency
        post_analyses.sort(key=lambda p: p.score, reverse=True)

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
                self._add_quotes(post_analysis, report, analysis.optimism, all_quotes.optimism)

        logger.info(
            f"Aggregated quotes: {len(all_quotes.fears)} fears, "
            f"{len(all_quotes.frustrations)} frustrations, "
            f"{len(all_quotes.optimism)} optimism"
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
            "optimism": {"mild": 0, "moderate": 0, "strong": 0},
        }
        for analysis in all_analyses:
            for key, result in [
                ("fears", analysis.fears),
                ("frustrations", analysis.frustrations),
                ("optimism", analysis.optimism),
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
            + list(all_quotes.optimism)
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

        if change_pct > settings.trend_threshold_pct:
            direction = TrendDirection.UP
        elif change_pct < -settings.trend_threshold_pct:
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
            "optimism": [q.text for q in all_quotes.optimism],
        }

    def get_post_titles_with_scores(self, subreddit_reports: list[SubredditReport]) -> list[str]:
        """Get post titles with scores for thematic clustering."""
        return [
            f"[+{post.score}] {post.title}"
            for report in subreddit_reports
            for post in report.top_posts
        ]

    def build_title_to_url_map(self, subreddit_reports: list[SubredditReport]) -> dict[str, str]:
        """Build a lookup map from post title to URL."""
        return {
            post.title: self._convert_to_new_reddit(post.url)
            for report in subreddit_reports
            for post in report.top_posts
        }

    def _convert_to_new_reddit(self, url: str) -> str:
        """Convert old.reddit.com URLs to www.reddit.com."""
        if url:
            return url.replace("old.reddit.com", "www.reddit.com")
        return url

    def enrich_thematic_clusters_with_urls(
        self,
        clusters: list[ThematicCluster],
        title_to_url: dict[str, str],
    ) -> list[ThematicCluster]:
        """Enrich thematic clusters by converting sample_posts strings to SamplePost objects with URLs."""
        enriched = []
        for cluster in clusters:
            enriched_posts = []
            for post in cluster.sample_posts:
                title = post if isinstance(post, str) else post.title
                url = self._find_url_for_title(title, title_to_url)
                enriched_posts.append(SamplePost(title=title, url=url))
            enriched.append(ThematicCluster(
                topic=cluster.topic,
                engagement_score=cluster.engagement_score,
                dominant_emotion=cluster.dominant_emotion,
                sample_posts=enriched_posts,
                entities=cluster.entities,
            ))
        return enriched

    def _find_url_for_title(self, title: str, title_to_url: dict[str, str]) -> str | None:
        """Find URL for a title, using fuzzy matching if exact match fails."""
        # Try exact match first
        if title in title_to_url:
            return title_to_url[title]

        # Normalize for comparison (lowercase, strip whitespace)
        normalized_title = title.lower().strip()
        for existing_title, url in title_to_url.items():
            if existing_title.lower().strip() == normalized_title:
                return url

        # Try substring match (LLM sometimes truncates titles)
        for existing_title, url in title_to_url.items():
            if normalized_title in existing_title.lower() or existing_title.lower() in normalized_title:
                return url

        return None
